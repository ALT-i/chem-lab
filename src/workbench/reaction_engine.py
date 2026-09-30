import math
from collections import OrderedDict
from chempy import balance_stoichiometry, Substance


ACID_PROTONS = {
    'HCL': 1,
    'HNO3': 1,
    'H2SO4': 2,
    'CH3COOH': 1,
    'H3PO4': 3,
    'HBR': 1,
    'HI': 1,
}

BASE_HYDROXIDES = {
    'NAOH': 1,
    'KOH': 1,
    'CA(OH)2': 2,
    'BA(OH)2': 2,
    'NH3': 1,
    'MG(OH)2': 2,
    'LIOH': 1,
}


def _canonical_formula(formula: str) -> str:
    return formula.strip().upper()


def get_acid_protons(formula: str) -> int:
    canon = _canonical_formula(formula)
    if canon in ACID_PROTONS:
        return ACID_PROTONS[canon]
    if formula.startswith('H') and len(formula) > 1 and formula[1].isupper():
        return 1
    return 0


def get_base_hydroxides(formula: str) -> int:
    canon = _canonical_formula(formula)
    if canon in BASE_HYDROXIDES:
        return BASE_HYDROXIDES[canon]
    if 'OH' in formula:
        if '(OH)2' in formula:
            return 2
        return 1
    return 0


def format_equation(reac_coeff: dict, prod_coeff: dict) -> str:
    left = ' + '.join(f"{v} {k}" if v > 1 else f"{k}" for k, v in reac_coeff.items())
    right = ' + '.join(f"{v} {k}" if v > 1 else f"{k}" for k, v in prod_coeff.items())
    return f"{left} -> {right}"


def calculate_reaction(reactants: list, products: list, reaction_type: str = None) -> dict:
    """
    Computes balanced stoichiometry, limiting reagents, product yields, and final pH.

    :param reactants: list of dicts with keys:
                      - formula (str, e.g. 'HCl')
                      - volume (float, mL or cm³)
                      - molarity (float, optional M)
                      - mass (float, optional grams for solid)
                      - moles (float, optional direct moles)
    :param products: list of str formulas (e.g. ['NaCl', 'H2O'])
    :param reaction_type: optional str hint ('neutralization', 'precipitation', 'redox', 'gas_evolution')
    """
    if not reactants or not products:
        raise ValueError("Reactants and products must not be empty.")

    reac_formulas = {r['formula'].strip() for r in reactants if r.get('formula')}
    prod_formulas = {p.strip() for p in products if p}

    if not reac_formulas or not prod_formulas:
        raise ValueError("Valid reactant and product formulas are required.")

    # 1. Balance stoichiometry via chempy
    reac_coeff, prod_coeff = balance_stoichiometry(reac_formulas, prod_formulas)

    # 2. Compute initial moles and extent of reaction
    total_volume_ml = 0.0
    initial_moles = {}
    extents = {}

    for r in reactants:
        formula = r['formula'].strip()
        vol_ml = float(r.get('volume', 0.0) or 0.0)
        total_volume_ml += vol_ml

        if 'moles' in r and r['moles'] is not None:
            n = float(r['moles'])
        elif 'mass' in r and r['mass'] is not None:
            sub = Substance.from_formula(formula)
            mw = float(sub.molar_mass())
            n = float(r['mass']) / mw if mw > 0 else 0.0
        elif 'molarity' in r and r['molarity'] is not None:
            c = float(r['molarity'])
            vol_l = vol_ml / 1000.0
            n = c * vol_l
        else:
            # Default to 0.1 M if molarity unspecified
            vol_l = vol_ml / 1000.0
            n = 0.1 * vol_l

        initial_moles[formula] = n
        coeff = float(reac_coeff.get(formula, 1))
        extents[formula] = n / coeff if coeff > 0 else n

    # 3. Determine limiting reagent
    sorted_extents = sorted(extents.items(), key=lambda item: item[1])
    min_formula, min_extent = sorted_extents[0]

    # Check if equimolar within small tolerance
    all_equal = all(abs(val - min_extent) < 1e-7 for _, val in sorted_extents)
    limiting_reagent = "Equimolar / None" if all_equal else min_formula
    max_extent = max(0.0, float(min_extent))

    # 4. Product yields
    yield_list = []
    for p, coeff in prod_coeff.items():
        n_formed = float(coeff) * max_extent
        try:
            sub = Substance.from_formula(p)
            mw = float(sub.molar_mass())
        except Exception:
            mw = 0.0
        yield_list.append({
            'formula': p,
            'theoretical_moles': round(float(n_formed), 6),
            'mass_g': round(float(n_formed * mw), 4) if mw > 0 else 0.0,
        })

    # 5. Excess / remaining reactants
    excess_list = []
    remaining_moles = {}
    for r in reactants:
        f = r['formula'].strip()
        n_initial = initial_moles.get(f, 0.0)
        coeff = float(reac_coeff.get(f, 1))
        n_consumed = coeff * max_extent
        n_remaining = max(0.0, n_initial - n_consumed)

        remaining_moles[f] = n_remaining

        rem_molarity = (n_remaining / (total_volume_ml / 1000.0)) if total_volume_ml > 0 else 0.0
        if n_remaining > 1e-7:
            excess_list.append({
                'formula': f,
                'excess_moles': round(n_remaining, 6),
                'remaining_molarity': round(rem_molarity, 4),
            })

    # 6. Final pH calculation
    is_acid_base = False
    total_h_moles = 0.0
    total_oh_moles = 0.0

    for f, n_rem in remaining_moles.items():
        protons = get_acid_protons(f)
        hydroxides = get_base_hydroxides(f)
        if protons > 0:
            is_acid_base = True
            total_h_moles += protons * n_rem
        if hydroxides > 0:
            is_acid_base = True
            total_oh_moles += hydroxides * n_rem

    vol_l = max(0.001, total_volume_ml / 1000.0)

    if is_acid_base or reaction_type == 'neutralization':
        net_h = total_h_moles - total_oh_moles
        if net_h > 1e-7:
            conc_h = net_h / vol_l
            final_ph = -math.log10(conc_h)
        elif -net_h > 1e-7:
            conc_oh = abs(net_h) / vol_l
            poh = -math.log10(conc_oh)
            final_ph = 14.0 - poh
        else:
            final_ph = 7.0
        final_ph = max(0.0, min(14.0, final_ph))
    else:
        # Neutral or precipitation
        final_ph = 7.0

    equation_str = format_equation(reac_coeff, prod_coeff)

    return {
        'balanced_equation': equation_str,
        'coefficients': {
            'reactants': {str(k): int(v) for k, v in reac_coeff.items()},
            'products': {str(k): int(v) for k, v in prod_coeff.items()},
        },
        'limiting_reagent': str(limiting_reagent),
        'excess_reagents': excess_list,
        'yield': yield_list,
        'final_ph': round(float(final_ph), 2),
        'total_volume': round(float(total_volume_ml), 2),
    }

