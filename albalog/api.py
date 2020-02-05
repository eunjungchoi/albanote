import calendar
from datetime import datetime, date, timedelta

from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed

from albalog.models import User, Business, Member, TimeTable, Attendance, HolidayPolicy, PayRoll


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


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ('id', 'license_name', 'license_number', 'address')


class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer

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
            'business': BusinessSerializer(business).data,
            'member': MemberSerialzer(member).data
        })


class MemberSerialzer(serializers.ModelSerializer):
    business = BusinessSerializer()
    user = UserSerializer()
    latest_work_date = serializers.SerializerMethodField('latest_work')

    class Meta:
        model = Member
        fields = ('id', 'business', 'user', 'type', 'hourly_wage', 'status', 'latest_work_date', 'created', 'annual_leave', 'start_date')

    def latest_work(self, obj):
        work = Attendance.objects.filter(member=obj, absence=False).last()
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
        insurances = request.data['insurance']
        member, created = Member.objects.get_or_create(
            user=new_user,
            business=business,
            type=type,
            hourly_wage=request.data['hourly_wage'],
            start_date=request.data['start_date'],
            weekly_holiday=request.data['weekly_holiday'],
            national_pension='0' in insurances,
            health_insurance='1' in insurances,
            employment_insurance='2' in insurances,
            industrial_accident_comp_insurance='3' in insurances
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
            return JsonResponse({ 'error': '근무일정 추가는 관리자만 가능합니다'})
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


class HolidayPolicySerializer(serializers.ModelSerializer):
    business = BusinessSerializer()

    class Meta:
        model = HolidayPolicy
        fields = ('id', 'business', 'type', 'paid', 'memo')


class HolidayPolicyViewSet(viewsets.ModelViewSet):
    queryset = HolidayPolicy.objects.all()
    serializer_class = HolidayPolicySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'business' in self.request.query_params:
            business = Business.objects.get(id=self.request.query_params['business'])
            queryset = queryset.filter(business__id=business.id)

        return queryset

    def create(self, request, *args, **kwargs):
        business = Business.objects.get(id=request.data['business_id'])
        holiday = HolidayPolicy.objects.create(
            business=business,
            type=request.data['type'],
            paid=request.data['paid'],
            memo=request.data['memo']
        )
        return JsonResponse(HolidayPolicySerializer(holiday).data)


class AttendanceSerializer(serializers.ModelSerializer):
    member = MemberSerialzer()

    class Meta:
        model = Attendance
        fields = ('member', 'start_time', 'end_time', 'duration', 'late_come', 'date', 'early_leave', 'absence', 'reason')


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects
    serializer_class = AttendanceSerializer

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
        if 'absence' in request.data and int(request.data['absence']) == 1:
            if request.data['reason'] == 2 and member.annual_leave == 0:
                return JsonResponse({'error': '남은 연차가 없습니다'})

            attendance = Attendance.objects.create(
                member=member,
                absence=True,
                date=request.data['date'],
                reason=request.data['reason'],
            )
        else:
            attendance = Attendance.objects.create(
                member=member,
                start_time=request.data['start_time'],
                end_time=request.data['end_time'],
                date=request.data['start_time'][0:10],
                absence=False,
            )
        return JsonResponse(AttendanceSerializer(attendance).data)

    @action(['get'], detail=False)
    def get_monthly_salary(self, request):
        queryset = super().get_queryset()
        business = Business.objects.get(id=request.query_params['business'])

        from datetime import date
        if 'year' in request.query_params and 'month' in request.query_params:
            year = int(request.query_params['year'])
            month = int(request.query_params['month'])
        else:
            today = datetime.today()
            year = today.year
            month = today.month
        last_day_of_month = date(year, month, calendar.monthrange(year, month)[1])

        me = Member.objects.get(business=business, user=request.user)
        if me.type == 'manager':
            members = Member.objects.filter(business=business)
        else:
            members = [me]

        all_members_salary = []
        save_payroll = False
        if 'save' in request.query_params:
            save_payroll = True

        for member in members:
            member_salary = self.calculate_monthly_salary(queryset, member, year, month, last_day_of_month, save_payroll)
            all_members_salary.append(member_salary)

        salary_data = {
                'year': year,
                'month': month,
                'members': all_members_salary
        }
        return JsonResponse(salary_data)

    def calculate_monthly_salary(self, queryset, member, year, month, last_day_of_month, save):
        queryset = queryset.filter(member=member)
        total_working_days, total_hours, base_salary, late_come_count = self.calculate_base_salary(queryset, member, year, month)

        from datetime import date
        today = date.today()
        주휴수당 = []
        weekly_hours = {}

        key_dates = [1, 8, 15, 22, 29]
        for i, key_date in enumerate(key_dates):
            from datetime import date
            date = date(year, month, key_date) - timedelta(days=1)
            start = date - timedelta(days=date.weekday())  # 월요일부터
            end = start + timedelta(days=6)  # 일요일까지
            pay = 0

            weekly_total_hours = self.weekly_total_hours(queryset, start, end)
            weekly_hours[start.strftime('%Y-%m-%d')] = weekly_total_hours

            if last_day_of_month <= end:break
            if today <= end:break
            if member.resignation_date and member.resignation_date <= end:break

            if weekly_total_hours >= 15 and self.attend_all(queryset, start, end, member):
                pay = self.calculate_weekly_holiday_pay(weekly_total_hours, member)

            주휴수당.append(pay)

        sum_of_weekly_holiday_pay = sum(주휴수당)
        gross_pay = base_salary + sum_of_weekly_holiday_pay
        sum_of_deductions = 0
        net_pay = gross_pay - sum_of_deductions

        if save:
            PayRoll.objects.get_or_create(
                member=member,
                year=year,
                month=month,
                working_hours=total_hours,
                working_days=total_working_days,
                base_salary=base_salary,
                weekly_holiday_allowance=sum_of_weekly_holiday_pay,
                gross_pay=gross_pay,
                sum_of_deductions=sum_of_deductions,
                net_pay=net_pay
            )
        return {
            'id': member.id,
            'total_hours': total_hours,
            'working_days': total_working_days,
            'late_come_count': late_come_count,
            'weekly_hours': weekly_hours,
            'total_monthly_pay': net_pay,
            'base_salary': base_salary,
            'total_extra_pay': sum_of_weekly_holiday_pay,
            'extra_pay_list': 주휴수당
        }

    def calculate_base_salary(self, queryset, member, year, month):
        total_working_days = queryset.filter(start_time__year=year, start_time__month=month, absence=False).count()
        late_come_count = queryset.filter(start_time__year=year, start_time__month=month, absence=False, late_come__isnull=False).count()
        total_work_duration = queryset.filter(absence=False, start_time__year=year, start_time__month=month).aggregate(Sum('duration'))['duration__sum']
        actual_work_hours = total_work_duration.total_seconds() // 3600 if total_work_duration else 0

        # 법정휴일이나 연차 사용일은 유급휴일로서, 근로한 것으로 인정해서 총 근로시간에 포함시켜줌
        queryset = queryset.filter(absence=True, reason__in=[0, 2], date__year=year, date__month=month)
        paid_leave_sum = None
        if queryset.count():
            for q in queryset:
                from datetime import date
                original_duration = datetime.combine(date.today(), q.timetable.end_time) - datetime.combine(date.today(), q.timetable.start_time)
                paid_leave_sum = paid_leave_sum + original_duration if paid_leave_sum else original_duration

        if paid_leave_sum:
            total_work_duration = total_work_duration + paid_leave_sum if total_work_duration else paid_leave_sum

        if total_work_duration:
            total_hours = total_work_duration.total_seconds() // 3600
            return total_working_days, actual_work_hours, total_hours * member.hourly_wage, late_come_count
        return 0, 0, 0, 0

    def weekly_total_hours(self, queryset, start, end):
        weekly_work_duration = queryset.filter(absence=False, start_time__gte=start, end_time__lte=end).aggregate(Sum('duration'))['duration__sum']

        # 유급휴일을 주 근로시간에 포함시켜 계산
        queryset = queryset.filter(absence=True, reason=2, date__gte=start, date__lte=end)
        if queryset.count():
            annual_leave_sum = None

            for q in queryset:
                from datetime import date
                original_duration = datetime.combine(date.today(), q.timetable.end_time) - datetime.combine(date.today(), q.timetable.start_time)
                annual_leave_sum = annual_leave_sum + original_duration if annual_leave_sum else original_duration

            if annual_leave_sum:
                weekly_work_duration = weekly_work_duration + annual_leave_sum if weekly_work_duration else annual_leave_sum

        if weekly_work_duration:
            return weekly_work_duration.total_seconds() // 3600
        return 0

    def attend_all(self, queryset, start, end, member):
        work = queryset.filter(absence=False, start_time__gte=start, end_time__lte=end).exclude(timetable__isnull=True)
        timetables = TimeTable.objects.filter(member=member)
        work_count = work.count()
        timetable_count = timetables.count()
        if not work_count:   # 실제 근로한 날이 0일이면 주휴수당 수령 불가
            return False

        if work_count == timetable_count:
            return True

        paid_leave = queryset.filter(absence=True, reason__in=[0, 2], date__gte=start, date__lte=end)

        if paid_leave.count() == timetable_count:  # 한 주가 모두 연차로 구성되면 주휴수당 수령 불가
            return False
        if work_count + paid_leave.count() == timetable_count:
            return True

        return False

    def calculate_weekly_holiday_pay(self, weekly_total_hours, member):
        if weekly_total_hours >= 40:
            return 8 * member.hourly_wage

        daily_average_hours = weekly_total_hours / 5
        return daily_average_hours * member.hourly_wage
