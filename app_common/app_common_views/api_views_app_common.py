from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from helpers import api_permission
from product.models import Category, Products
from product.serializers import CategorySerializer, ProductsSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from app_common.models import Banner
from users.user_views.emails import send_template_email
from users.serializers import BannerSerializer, ContactMessageSerializer


class HomeAPIView(APIView):
    
    @swagger_auto_schema(
        tags=["Home"],
        operation_description="Retrieve home page data including categories, trending products, and new products.",
        responses={
            200: 'Successful response with categories, trending products, and new products',
            404: 'Not found',
            500: 'Internal server error',
        }
    )
    def get(self, request):
        if request.user.is_superuser:
            return Response({"detail": "Redirecting to admin dashboard"}, status=status.HTTP_302_FOUND)

        # Get all categories
        categories = Category.objects.all()
        category_serializer = CategorySerializer(categories, many=True)

        # Handle Trending Products
        trending_products = Products.objects.filter(trending="yes").order_by('-id')[:7]
        trending_product_serializer = ProductsSerializer(trending_products, many=True)

        # Handle New Products
        new_products = Products.objects.filter(show_as_new="yes").order_by('-id')[:7]
        new_product_serializer = ProductsSerializer(new_products, many=True)

        context = {
            'categories': category_serializer.data,
            'trending_products': trending_product_serializer.data,
            'new_products': new_product_serializer.data,
            'MEDIA_URL': settings.MEDIA_URL,
        }

        return Response(context, status=status.HTTP_200_OK)
    

class ContactSupportAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Support"],
        operation_description="Retrieve initial contact form data for authenticated users.",
        responses={
            200: "Initial data successfully retrieved.",
            401: "Authentication credentials were not provided or are invalid.",
        }
    )
    def get(self, request, *args, **kwargs):
        initial_data = {
            'name': request.user.full_name if request.user.is_authenticated and hasattr(request.user, 'full_name') else '',
            'email': request.user.email if request.user.is_authenticated else '',
            'contact': request.user.contact if request.user.is_authenticated and hasattr(request.user, 'contact') else ''
        }
        return Response(initial_data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["Support"],
        operation_description="Submit a contact message for support.",
        request_body=ContactMessageSerializer,
        responses={
            201: "Message successfully submitted.",
            400: "Invalid form data.",
            404: "User not found.",
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            contact_message = serializer.save()
            
            if request.user.is_authenticated:
                contact_message.user = request.user
                contact_message.save()

            # Sending a confirmation email
            context = {
                'user_name': contact_message.name,
                'message_content': contact_message.message,
            }
            send_template_email(
                subject='Thank You for Contacting Us',
                template_name='users/email/contact_message_confirmation.html',
                context=context,
                recipient_list=[contact_message.email]
            )

            return Response({'message': 'Your message has been sent successfully.'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class BannerListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        tags=["Banner API"],
        operation_description="Retrieve list of active banners",
        responses={200: BannerSerializer(many=True)}
    )
    def get(self, request):
        banners = Banner.objects.filter(active=True).order_by('order')
        serializer = BannerSerializer(banners, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)