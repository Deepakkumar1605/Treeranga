from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from blog.models import Blogs
from blog.serializers import BlogSerializer
from cart.models import Cart

class BlogListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Blogs"],
        operation_description="Retrieve all blog posts.",
        responses={200: 'Successful response with all blog posts'}
    )
    def get(self, request):
        blogs = Blogs.objects.all()
        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BlogDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Blogs"],
        operation_description="Retrieve blog post details by slug.",
        responses={
            200: 'Successful response with blog post details',
            404: 'Blog post not found'
        }
    )
    def get(self, request, slug):
        blog = get_object_or_404(Blogs, slug=slug)
        serializer = BlogSerializer(blog)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Cart"],
        operation_description="Remove a product from the cart.",
        responses={
            200: 'Product removed from cart successfully.',
            404: 'Product not found in cart.',
            400: 'Bad Request',
        }
    )
    def delete(self, request, cp_uid):
        try:
            if request.user.is_authenticated:
                cart = get_object_or_404(Cart, user=request.user)
                if cp_uid in cart.products:
                    cart.products.pop(cp_uid)
                    cart.total_price = sum(item['total_price'] for item in cart.products.values())
                    cart.save()
                    return Response({"success": "Product removed from cart successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)
            else:
                cart = request.session.get('cart', {'products': {}})
                products = cart.get('products', {})
                if cp_uid in products:
                    products.pop(cp_uid)
                    cart['total_price'] = sum(item['total_price'] for item in products.values())
                    cart['products'] = products
                    request.session['cart'] = cart
                    request.session.modified = True
                    return Response({"success": "Product removed from cart successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Product not found in cart."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Error while removing product from cart: {e}")
            return Response({"error": "An error occurred while removing the product from the cart."}, status=status.HTTP_400_BAD_REQUEST)