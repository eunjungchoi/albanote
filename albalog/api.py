from django.http import JsonResponse
from requests import Response
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed

from albalog.models import User, Business, Member, Work


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'name', 'phone', 'sex')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(['get'], detail=False)
    def me(self, request):
        if not request.user.is_authenticated:
            raise AuthenticationFailed('로그인 정보를 찾을 수 없습니다.')
        return JsonResponse(UserSerializer(request.user).data)


class BusinessSerialzer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ('id', 'license_name', 'license_number', 'address')


class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerialzer


class MemberSerialzer(serializers.ModelSerializer):
    business = BusinessSerialzer()
    user = UserSerializer()

    class Meta:
        model = Member
        fields = ('id', 'business', 'user', 'type')


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerialzer

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class WorkSerializer(serializers.ModelSerializer):
    member = MemberSerialzer()

    class Meta:
        model = Work
        fields = ('member', 'start_time', 'end_time', 'duration', 'hourly_wage')


class WorkViewSet(viewsets.ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer

    def get_queryset(self):
        queryset = super().get_queryset().filter(member__user=self.request.user)
        if 'business' in self.request.query_params:
            queryset = queryset.filter(member__business__id=self.request.query_params['business'])
        queryset = queryset.order_by('-start_time')
        return queryset
