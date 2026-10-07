from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from rest_framework import generics, status
from rest_framework.views import APIView


from .models import *
from .serializers import *
from .grading import calculate_session_grade, evaluate_measurement_step
from src.common.moodle_client import MoodleClient
from src.users.permissions import IsInstructorOrAdmin

# Create your views here.

class LessonViewSet(ModelViewSet):
    """
        CRUD operations on Lesson objects
    """
    queryset  = Lesson.objects.all()
    serializer_class =  LessonSerializer
    # filterset_fields = ['title']

    def get_queryset(self):                                      
        return super().get_queryset()
    
    # def perform_create(self, serializer):
    #     # In case of using the serializer 
    #     serializer.save()
        
    def create(self, request, *args, **kwargs):
        # Regular logic going through the serializer
        # serializer = self.get_serializer(data=request.data)
        # try:
        #   serializer.is_valid(raise_exception=True)
        # except Exception as e :
        #   return Response({"message": e}, status=status.HTTP_400_BAD_REQUEST)
        # self.perform_create(serializer)
        # headers = self.get_success_headers(serializer.data)
        
        # Removing instructor, tools and substances from payload to avoid complications
        tools = request.data.pop('tools')    
        substances = request.data.pop('substances')
           
        
        # Creating lesson 
        lesson = Lesson.objects.create(**request.data)
        
        # Saving instructor, tools and substances to created lesson 
        lesson.tools.set(tools)
        lesson.substances.set(substances)
        lesson.save()
        
        # Serializing lesson instance for response data 
        serializer = self.get_serializer(lesson)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Lesson created successfully", "data": serializer.data}, 
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def list(self, request):
        queryset = self.get_queryset()
        queryset = self.queryset.filter(
            title__icontains = request.query_params.get('search') if request.query_params.get('search') else '',
            instructor__id__contains = request.query_params.get('instructor') if request.query_params.get('instructor') else ''
        )
        try:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({"message": "Lessons retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"message":"Lesson retrived successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def perform_update(self, serializer):
        serializer.save()
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except:
            return Response({"message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response({"message": "Lesson updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)        
        
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        if 'instructor' in request.data.keys():
            instructor = User.objects.get(id = request.data['instructor'])
            lesson = Lesson.objects.get(id = kwargs['pk'])
            lesson.instructor = instructor
            lesson.save()
        
        if 'substances' in request.data.keys():
            substances = request.data['substances']
            lesson = Lesson.objects.get(id = kwargs['pk'])
            lesson.substances.set(substances)
            lesson.save()
        
        if 'tools' in request.data.keys():
            tools = request.data['tools']
            lesson = Lesson.objects.get(id = kwargs['pk'])
            lesson.tools.set(tools)
            lesson.save()
        
        return self.update(request, *args, **kwargs)


# Moodle integration endpoints

class MoodleStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    def get(self, request, *args, **kwargs):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({'detail': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course_int = int(course_id)
        except ValueError:
            return Response({'detail': 'course_id must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        client = MoodleClient()
        users = client.get_enrolled_users(course_int)
        return Response(users, status=status.HTTP_200_OK)


class MoodleUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        email = request.query_params.get('email')
        if not email:
            return Response({'detail': 'email is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client = MoodleClient()
            users = client.get_users_by_email([email])
            if not users or len(users) == 0:
                return Response({
                    'detail': f'User not found in Moodle with email: {email}',
                    'searched_email': email
                }, status=status.HTTP_404_NOT_FOUND)
            return Response(users[0], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Error fetching from Moodle: {str(e)}',
                'searched_email': email
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MoodleAssignmentGradesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        course_id = data.get('course_id')
        assignment_id = data.get('assignment_id')
        grades = data.get('grades') or []
        if course_id is None or assignment_id is None:
            return Response({'detail': 'course_id and assignment_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course_int = int(course_id)
            assignment_int = int(assignment_id)
        except ValueError:
            return Response({'detail': 'course_id and assignment_id must be integers'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(grades, list) or len(grades) == 0:
            return Response({'detail': 'grades must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

        client = MoodleClient()
        enrolled = client.get_enrolled_users(course_int)
        enrolled_by_email = {u.get('email'): u for u in enrolled if u.get('email')}

        results = []
        for entry in grades:
            email = (entry or {}).get('email')
            grade_value = (entry or {}).get('grade')
            feedback = (entry or {}).get('feedback')
            session_id = (entry or {}).get('session_id')

            # Dynamic grading evaluation from session if grade is not explicitly given or if session_id passed
            if grade_value is None and session_id:
                try:
                    session = LessonSession.objects.get(id=session_id)
                    eval_res = calculate_session_grade(session.measurements or {})
                    grade_value = eval_res['overall_grade']
                    if not feedback:
                        feedback = eval_res['feedback']
                except Exception:
                    pass

            if not email or grade_value is None:
                results.append({'email': email, 'status': 'error', 'detail': 'email and grade are required'})
                continue
            if email not in enrolled_by_email:
                users = client.get_users_by_email([email])
                user = users[0] if users else None
                if not user:
                    results.append({'email': email, 'status': 'error', 'detail': 'user not found'})
                    continue
                user_id = user.get('id')
            else:
                user_id = enrolled_by_email[email].get('id')

            try:
                client.save_assignment_grade(assignment_int, int(user_id), float(grade_value), feedback)
                results.append({'email': email, 'status': 'ok', 'user_id': user_id, 'grade': grade_value})
            except Exception as exc:
                results.append({
                    'email': email,
                    'status': 'error',
                    'detail': str(exc),
                    'user_id': user_id,
                    'assignment_id': assignment_int,
                    'grade': grade_value
                })

        return Response({'results': results}, status=status.HTTP_200_OK)


class LessonSessionViewSet(ModelViewSet):
    """
    CRUD operations on LessonSession objects with student telemetry persistence
    and dynamic accuracy/precision grading evaluation.
    """
    queryset = LessonSession.objects.all().select_related('lesson', 'student')
    serializer_class = LessonSessionSerializer

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if 'student' not in serializer.validated_data and user.is_authenticated:
            serializer.save(student=user)
        else:
            serializer.save()

    @action(detail=True, methods=['get', 'post'], url_path='evaluate-grade')
    def evaluate_grade(self, request, pk=None):
        session = self.get_object()
        if request.method == 'POST' and 'measurements' in request.data:
            session.measurements = request.data['measurements']
            session.save(update_fields=['measurements'])
        evaluation = calculate_session_grade(session.measurements or {})
        return Response({
            'status': 'ok',
            'session_id': str(session.id),
            'evaluation': evaluation,
        }, status=status.HTTP_200_OK)