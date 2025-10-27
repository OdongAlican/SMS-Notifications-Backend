from pride_notify_notice.serializers import GroupSMSLogSerializer, SendEmailSerializer, SendSMSSerializer
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import views
from rest_framework import status
from django.utils import timezone
from datetime import datetime
from pride_notify_notice.models import GroupSMSLog, SMSLog, BirthdaySMSLog
from pride_notify_notice.serializers import SMSLogSerializer, BirthdaySMSLogSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from users.utils import CustomGroupPermissionAssignment

# Create your views here.
class Sms(views.APIView):
    def post(self, request: Request):
        serializer = SendSMSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.save()


class Email(views.APIView):
    def post(self, request: Request) -> Response:
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": 1,
            "message": "Email has been sent successfully"}, status=status.HTTP_200_OK)

class SMSLogsForMonthView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,CustomGroupPermissionAssignment]

    def _get_filtered_loan_logs(self, start_date, end_date):
        """Helper method to get filtered logs based on date range"""
        return SMSLog.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')  # Adding ordering to fix the warning
    
    def getLoansReport(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        page_size = request.query_params.get('page_size', 10)  # Default to 10 if not provided
        page_size = int(page_size)  # Ensure page_size is an integer

        if not start_date or not end_date:
            return Response({"error": "Please provide both start_date and end_date."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert string to datetime objects (assuming ISO 8601 format)
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            
            # Adjust the end_date to the end of the day (23:59:59.999999)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        except ValueError:
            return Response({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetching the SMS logs for the custom date range where the status is 'Success'
        successful_logs = SMSLog.objects.filter(
            # status='000|ACCEPTED FOR DELIVERY',
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Pagination setup
        paginator = PageNumberPagination()
        paginator.page_size = page_size  # Dynamically set the page size
        paginated_logs = paginator.paginate_queryset(successful_logs, request)

        # Serialize the paginated logs
        serializer = SMSLogSerializer(paginated_logs, many=True)

        # Response data with count and pagination info
        response_data = {
            'count': successful_logs.count(),  # Total count of records
            'logs': serializer.data,
            'pagination': {
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'per_page': paginator.page_size,
                'total_records': successful_logs.count()
            }
        }

        return paginator.get_paginated_response(response_data)
    
    def exportLoansReport(self, request):
        """Export all loan SMS logs based on date range as JSON"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({"error": "Please provide both start_date and end_date."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return Response({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)

        # Get all logs without pagination
        logs = self._get_filtered_loan_logs(start_date, end_date)
        serializer = SMSLogSerializer(logs, many=True)
        
        # Return all data for export
        return Response({
            "data": serializer.data,
            "count": logs.count(),
            "date_range": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
        })
    
class BirthDaySMSView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,CustomGroupPermissionAssignment]

    def _get_filtered_birthday_logs(self, start_date, end_date):
        """Helper method to get filtered birthday logs based on date range"""
        return BirthdaySMSLog.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')  # Adding ordering to fix the warning
    
    def getBirthdayReport(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        page_size = request.query_params.get('page_size', 10)  # Default to 10 if not provided
        page_size = int(page_size)  # Ensure page_size is an integer

        if not start_date or not end_date:
            return Response({"error": "Please provide both start_date and end_date."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert string to datetime objects (assuming ISO 8601 format)
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            
            # Adjust the end_date to the end of the day (23:59:59.999999)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        except ValueError:
            return Response({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetching the SMS logs for the custom date range where the status is 'Success'
        successful_logs = BirthdaySMSLog.objects.filter(
            # status='000|ACCEPTED FOR DELIVERY',
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Pagination setup
        paginator = PageNumberPagination()
        paginator.page_size = page_size  # Dynamically set the page size
        paginated_logs = paginator.paginate_queryset(successful_logs, request)

        # Serialize the paginated logs
        serializer = BirthdaySMSLogSerializer(paginated_logs, many=True)

        # Response data with count and pagination info
        response_data = {
            'count': successful_logs.count(),  # Total count of records
            'logs': serializer.data,
            'pagination': {
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'per_page': paginator.page_size,
                'total_records': successful_logs.count()
            }
        }

        return paginator.get_paginated_response(response_data)
    
    def exportBirthdayReport(self, request):
        """Export all birthday SMS logs based on date range as JSON"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({"error": "Please provide both start_date and end_date."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return Response({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)

        # Get all logs without pagination
        logs = self._get_filtered_birthday_logs(start_date, end_date)
        serializer = BirthdaySMSLogSerializer(logs, many=True)
        
        # Return all data for export
        return Response({
            "data": serializer.data,
            "count": logs.count(),
            "date_range": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
        })
    
class GroupSMSView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,CustomGroupPermissionAssignment]

    def _get_filtered_group_logs(self, start_date, end_date):
        """Helper method to get filtered group logs based on date range"""
        return GroupSMSLog.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')  # Adding ordering to fix the warning
    
    def getGroupReport(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        page_size = request.query_params.get('page_size', 10)  # Default to 10 if not provided
        page_size = int(page_size)  # Ensure page_size is an integer

        if not start_date or not end_date:
            return Response({"error": "Please provide both start_date and end_date."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert string to datetime objects (assuming ISO 8601 format)
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            
            # Adjust the end_date to the end of the day (23:59:59.999999)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        except ValueError:
            return Response({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)
        

        # Fetching the SMS logs for the custom date range where the status is 'Success'
        successful_logs = GroupSMSLog.objects.filter(
            # status='000|ACCEPTED FOR DELIVERY',
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Pagination setup
        paginator = PageNumberPagination()
        paginator.page_size = page_size  # Dynamically set the page size
        paginated_logs = paginator.paginate_queryset(successful_logs, request)

        # Serialize the paginated logs
        serializer = GroupSMSLogSerializer(paginated_logs, many=True)

        # Response data with count and pagination info
        response_data = {
            'count': successful_logs.count(),  # Total count of records
            'logs': serializer.data,
            'pagination': {
                'total_pages': paginator.page.paginator.num_pages,
                'current_page': paginator.page.number,
                'per_page': paginator.page_size,
                'total_records': successful_logs.count()
            }
        }

        return paginator.get_paginated_response(response_data)
    
    
    def exportGroupReport(self, request):
        """Export all group SMS logs based on date range as JSON"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({"error": "Please provide both start_date and end_date."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return Response({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}, status=status.HTTP_400_BAD_REQUEST)

        # Get all logs without pagination
        logs = self._get_filtered_group_logs(start_date, end_date)
        serializer = GroupSMSLogSerializer(logs, many=True)
        
        # Return all data for export
        return Response({
            "data": serializer.data,
            "count": logs.count(),
            "date_range": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d')
            }
        })