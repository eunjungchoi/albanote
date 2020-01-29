from django.http import JsonResponse
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

    def create(self, request, *args, **kwargs):
        business = Business.objects.create(
            license_name=request.data['license_name'],
            license_number=request.data['license_number'],
            address=request.data['address']
        )
        member = Member.objects.create(
            business=business,
            user=request.user,
            type='manager'
        )
        return JsonResponse({
            'business': BusinessSerialzer(business).data,
            'member': MemberSerialzer(member).data
        })


class MemberSerialzer(serializers.ModelSerializer):
    business = BusinessSerialzer()
    user = UserSerializer()

    class Meta:
        model = Member
        fields = ('id', 'business', 'user', 'type', 'hourly_wage', 'created')


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerialzer

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    @action(['get'], detail=False)
    def all_members_of_business(self, request):
        business_id = request.query_params['business']
        member = Member.objects.filter(user=request.user, business__id=int(business_id))[0]
        if member.type != 'manager':
            return JsonResponse({ 'error': '직원 목록은 관리자만 볼 수 있습니다'})

        queryset = self.queryset.filter(business__id=request.query_params['business'])
        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(serializer.data, safe=False)

    def create(self, request, *args, **kwargs):
        new_user = User.objects.get(username=request.data['user_id'])
        business = Business.objects.get(id=request.data['business_id'])

        me = Member.objects.get(user=request.user, business=business)
        if me.type != 'manager':
            return JsonResponse({ 'error': '직원 추가는 관리자만 가능합니다'})

        type = 'member'  # 관리자 1명을 제외한 모든 근로자는 일반 직원으로 분류
        member = Member.objects.create(
            user=new_user,
            business=business,
            type=type
        )
        return JsonResponse(MemberSerialzer(member).data)


class WorkSerializer(serializers.ModelSerializer):
    member = MemberSerialzer()

    class Meta:
        model = Work
        fields = ('member', 'start_time', 'end_time', 'duration')


class WorkViewSet(viewsets.ModelViewSet):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'business' in self.request.query_params:
            business = Business.objects.get(id=self.request.query_params['business'])
            queryset = queryset.filter(member__business__id=business.id)
            member = Member.objects.get(user=self.request.user, business=business)

            if member.type == 'member':
                queryset = queryset.filter(member__user=self.request.user)

        else:
            queryset = queryset.filter(member__user=self.request.user)

        queryset = queryset.order_by('-start_time')
        return queryset

    def create(self, request, *args, **kwargs):
        business_id = request.data['business_id']
        member = Member.objects.get(user=request.user, business__id=business_id)
        work = Work.objects.create(
            member=member,
            start_time=request.data['start_time'],
            end_time=request.data['end_time'],
        )
        return JsonResponse(WorkSerializer(work).data)

