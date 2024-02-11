import random
from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import generics, status
from chempy import Substance as chmSubstance
from chempy import balance_stoichiometry, Reaction, Equilibrium
from chempy.kinetics.ode import get_odesys
from scipy.integrate import solve_ivp

from .models import *
from .serializers import *

# Create your views here.

class LessonViewSet(ModelViewSet):
    """
        CRUD operations on Lesson objects
    """
    queryset  = Lesson.objects.all().order_by('title')
    serializer_class =  LessonSerializer

    def get_queryset(self):                                      
        return super().get_queryset()
    

# class ReactionListCreateView(generics.ListCreateAPIView):
#     queryset = Reaction.objects.all()
#     serializer_class = ReactionSerializer

#     def perform_create(self, serializer):
#         super().perform_create(serializer)
#         substances = Reaction.objects.values_list('substance', flat=True)
#         volumes = Reaction.objects.values_list('volume', flat=True)
#         reaction_result = balance_stoichiometry(substances, volumes)
#         return reaction_result

class ReactionViewSet(ModelViewSet):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer

    def create(self, request, *args, **kwargs):
        substances = request.data.get('substance', [])
        volumes = request.data.get('volume', [])

        data = request.data

        acid_formula = data.get('substance', '')[0]
        base_formula = data.get('substance', '')[1]
        acid_volume = data.get('volume', 0)[0]
        base_volume = data.get('volume', 0)[1]

        if acid_volume <= 0 or base_volume <= 0 or not acid_formula or not base_formula:
            return Response({'error': 'Invalid input data.'}, status=400)

        # Define substances
        acid = chmSubstance.from_formula(acid_formula).name
        base = chmSubstance.from_formula(base_formula).name


        # print(acid[1:],acid[:1], base[0:], base[:1])

         # Balance the reaction equation
        reactants = {acid, base}
        products = {acid[:1], acid[1:], base[:2], base[2:]}

        # print(reactants, products)

        balanced_reaction = balance_stoichiometry(reactants, products)

        # print(balanced_reaction)
        

        # Set up the equilibrium
        equilibrium = Equilibrium(reactants, products)

        # Define initial concentrations
        initial_concentrations = {acid: 0.1, base: 0.1}

        # Define the titration function
        def titration(t, concentrations):
            return equilibrium.Q * concentrations[acid] - concentrations[base]

        # Simulate the titration using solve_ivp
        result = solve_ivp(titration, (0, acid_volume), list(initial_concentrations.values()), method='LSODA')


        # Get the final concentrations
        final_concentrations = result.y[:, -1]

        balanced_reaction_list = [{'reactants': reactants, 'products': products}]

        result_dict = {
            'acid_formula': acid_formula,
            'base_formula': base_formula,
            'acid_volume': acid_volume,
            'base_volume': base_volume,
            'reaction_equation': balanced_reaction_list,
            'final_concentrations': dict(zip(initial_concentrations.keys(), final_concentrations))
        }

        return Response({"reactions": dict(result_dict)}, status=status.HTTP_201_CREATED)
    




# class TitrationExperimentViewSet(ModelViewSet):
#     # ...

#     @action(detail=True, methods=['post'])
#     def simulate_titration(self, request, pk=None):
#         experiment = self.get_object()

#         # Extract parameters from the request
#         initial_solution_volume = request.data.get('initial_solution_volume', 50)  # Initial volume in the flask
#         titrant_concentration = request.data.get('titrant_concentration', 0.1)  # Titrant concentration (mol/L)

#         # Simulate errors and variations in initial solution concentration
#         initial_solution_concentration = random.uniform(0.9, 1.1) * experiment.initial_solution_concentration

#         # Simulate the addition of titrant in random increments
#         total_titrant_volume = 0
#         while total_titrant_volume < initial_solution_volume:
#             titrant_increment = random.uniform(0.5, 2.0)  # Random volume increment added in each step
#             total_titrant_volume += titrant_increment

#             # Check if the reaction is complete (e.g., by reaching an equivalence point)
#             # Simulate reaction completion with a certain probability
#             reaction_complete = random.uniform(0, 1) < 0.1  # 10% chance of completion in each step

#             if reaction_complete:
#                 break

#         # Calculate the resulting solution concentration after titration
#         final_solution_volume = initial_solution_volume + total_titrant_volume
#         final_solution_concentration = (titrant_concentration * total_titrant_volume) / final_solution_volume

#         # Update experiment data
#         experiment.initial_solution_volume = initial_solution_volume
#         experiment.titrant_concentration = titrant_concentration
#         experiment.initial_solution_concentration = initial_solution_concentration
#         experiment.total_titrant_volume = total_titrant_volume
#         experiment.final_solution_volume = final_solution_volume
#         experiment.final_solution_concentration = final_solution_concentration

#         experiment.save()

#         return Response({
#             'status': 'Titration simulation completed',
#             'final_solution_concentration': final_solution_concentration
#         })