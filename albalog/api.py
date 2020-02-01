import calendar
from datetime import datetime, timedelta

from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed

from albalog.models import User, Business, Member, Work, TimeTable


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
    latest_work_date = serializers.SerializerMethodField('latest_work')

    class Meta:
        model = Member
        fields = ('id', 'business', 'user', 'type', 'hourly_wage', 'status', 'latest_work_date', 'created')

    def latest_work(self, obj):
        work = Work.objects.filter(member=obj).last()
        if work:
            return work.start_time
        else:
            return None


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
        member, created = Member.objects.get_or_create(
            user=new_user,
            business=business,
            type=type,
            hourly_wage=request.data['hourly_wage']
        )
        return JsonResponse(MemberSerialzer(member).data)


class TimeTableSerializer(serializers.ModelSerializer):
    member = MemberSerialzer()

    class Meta:
        model = TimeTable
        fields = ('member', 'day', 'start_time', 'end_time')


class TimeTableViewSet(viewsets.ModelViewSet):
    queryset = TimeTable.objects.all()
    serializer_class = TimeTableSerializer

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

        queryset = queryset.order_by('day')
        return queryset

    def create(self, request, *args, **kwargs):
        business_id = request.data['business_id']
        me = Member.objects.get(user=request.user, business__id=business_id)
        if me.type != 'manager':
            return JsonResponse({ 'error': '직원 추가는 관리자만 가능합니다'})
        if request.data['member']:
            member = Member.objects.filter(business_id=business_id).get(id=request.data['member'])
        else:
            member = me

        days = request.data['day']
        for day in days:
            TimeTable.objects.create(
                member=member,
                day=day,
                start_time=request.data['start_time'],
                end_time=request.data['end_time'],
            )
        return JsonResponse({'result': 'success'})


class WorkSerializer(serializers.ModelSerializer):
    member = MemberSerialzer()

    class Meta:
        model = Work
        fields = ('member', 'start_time', 'end_time', 'duration', 'late_come', 'early_leave')


class WorkViewSet(viewsets.ModelViewSet):
    queryset = Work.objects
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

        if 'year' in self.request.query_params and 'month' in self.request.query_params:
            queryset = queryset.filter(start_time__year=self.request.query_params['year'], start_time__month=self.request.query_params['month'])

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

    @action(['get'], detail=False)
    def get_monthly_salary(self, request):
        queryset = super().get_queryset()
        business = Business.objects.get(id=request.query_params['business'])
        me = Member.objects.get(business=business, user=request.user)
        if 'member' in request.query_params and me.type == 'manager':
            member = Member.objects.filter(business=business).get(id=request.query_params['member'])
        else:
            member = me
        queryset = queryset.filter(member=member)

        from datetime import date

        if 'year' in request.query_params and 'month' in request.query_params:
            year = int(request.query_params['year'])
            month = int(request.query_params['month'])
        else:
            today = datetime.today()
            year = today.year
            month = today.month

        last_day_of_month = date(year, month, calendar.monthrange(year, month)[1])

        # 기본급 계산
        total_hours, base_salary = self.calcuate_base_salary(queryset, member, year, month)

        # 2) 주휴수당 계산:
        주휴수당 = []
        key_dates = [1, 8, 15, 22, 29]
        for key_date in key_dates:
            from datetime import date
            date = date(year, month, key_date) - timedelta(days=1)
            start = date - timedelta(days=date.weekday())  # 월요일부터
            end = start + timedelta(days=6)  # 일요일까지
            pay = 0

            if last_day_of_month <= end:
                break
            weekly_total_hours = self.weekly_total_hours(queryset, start, end)
            if weekly_total_hours >= 15 and self.attend_all(queryset, start, end, member) and member.status == 'active':
                pay = self.calculate_extra_pay(weekly_total_hours, member)

            주휴수당.append(pay)

        total_extra_pay = sum(주휴수당)

        total_monthly_pay = base_salary + total_extra_pay
        data = {
                'year': year,
                'month': month,
                'total_hours': total_hours,
                'total_monthly_pay': total_monthly_pay,
                'base_salary': base_salary,
                'total_extra_pay': total_extra_pay,
                'extra_pay_list': 주휴수당 }
        return JsonResponse(data)


    def calcuate_base_salary(self, queryset, member, year, month):
        queryset = queryset.filter(start_time__year=year, start_time__month=month)
        total_work_duration = queryset.aggregate(Sum('duration'))['duration__sum']
        if total_work_duration:
            total_hours = total_work_duration.total_seconds() // 3600
            return total_hours, total_hours * member.hourly_wage
        return 0, 0

    def weekly_total_hours(self, queryset, start, end):
        queryset = queryset.filter(start_time__gte=start, end_time__lte=end)
        weekly_work_duration = queryset.aggregate(Sum('duration'))['duration__sum']
        if weekly_work_duration:
            return weekly_work_duration.total_seconds() // 3600
        return 0

    def attend_all(self, queryset, start, end, member):
        queryset = queryset.filter(start_time__gte=start, end_time__lte=end).order_by('start_time')
        timetables = TimeTable.objects.filter(member=member).order_by('day')

        queryset = queryset.exclude(timetable=None)
        if queryset.count() == timetables.count():
            return True

        absent_count = timetables.count() - queryset.count()
        return False

    def calculate_extra_pay(self, weekly_total_hours, member):  # 주휴수당 계산
        if weekly_total_hours >= 40:
            return 8 * member.hourly_wage

        daily_average_hours = weekly_total_hours / 5
        return daily_average_hours * member.hourly_wage
