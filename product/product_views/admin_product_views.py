from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.conf import settings
from app_common.error import render_error_page
from helpers import utils
from os.path import join
import json
from product_variations.models import Attribute, Variant, VariantImageGallery, VariantProduct
from product.models import Category, DeliverySettings,Products,SimpleProduct,ImageGallery,ProductReview
from itertools import product
from product import forms
import os
from django.core.files.storage import default_storage

app = "product/"





@method_decorator(utils.super_admin_only, name='dispatch')
class CategoryList(View):
    model = Category
    template = app + "admin/category_list.html"

    def get(self, request):
        try:
            catagory_list = self.model.objects.all().order_by('-id')
            context = {
                "catagory_list": catagory_list,
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class CatagoryAdd(View):
    model = Category
    form_class = forms.CategoryEntryForm
    template = app + "admin/category_add.html"

    def get(self, request):
        try:
            category_list = self.model.objects.all().order_by('-id')
            context = {
                "category_list": category_list,
                "form": self.form_class,
            }
            return render(request, self.template, context)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request):
        try:
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, f"Category added successfully.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            return redirect("product:category_list")
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class CategoryUpdate(View):
    model = Category
    form_class = forms.CategoryEntryForm
    template = app + "admin/category_update.html"

    def get(self, request, category_id):
        try:
            category = get_object_or_404(self.model, id=category_id)
            form = self.form_class(instance=category)
            return render(request, self.template, {'form': form})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request, category_id):
        try:
            category = get_object_or_404(self.model, id=category_id)
            form = self.form_class(request.POST, request.FILES, instance=category)
            if form.is_valid():
                form.save()
                messages.success(request, f"{category.title} updated successfully.")
                return redirect("product:category_list")
            else:
                messages.error(request, "Form is not valid. Please check the errors.")
                return render(request, self.template, {'form': form})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)


@method_decorator(utils.super_admin_only, name='dispatch')
class CatagotyDelete(View):
    model = Category
    form_class = forms.CategoryEntryForm
    template = app + "admin/category_update.html"

    def get(self, request, catagory_id):
        try:
            catagory = self.model.objects.get(id=catagory_id).delete()
            messages.info(request, "Category is deleted successfully....")
            return redirect("product:category_list")
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class ProductAdd(View):
    form_class = forms.ProductForm
    template_name = app + 'admin/product_add.html'  # Ensure this path is correct

    def get(self, request):
        form = self.form_class()
        context = {
            "form": form,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Save the product
                product = form.save(commit=False)
                if not product.uid:
                    product.uid = utils.get_rand_number(5)
                product.save()

                if product.product_type == "simple":
                    simple_product_obj = SimpleProduct(product=product, is_visible=False)
                    simple_product_obj.save()
                    messages.success(request, "Product added successfully.")
                    return JsonResponse({
                        'variant_types': None,
                        'product_id': product.id,
                    })
                elif product.product_type == "variant":
                    variant_types = Variant.objects.all().values('id', 'name')
                    return JsonResponse({
                        'variant_types': list(variant_types),
                        'product_id': product.id,
                    })
            except Exception as e:
                error_message = f"An unexpected error occurred: {str(e)}"
                print(error_message)
                return render_error_page(request, error_message, status_code=400)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        context = {
            "form": form,
        }
        return render(request, self.template_name, context)


def get_attributes(request, variant_type_id):
    try:
        attributes = Attribute.objects.filter(variant_type=variant_type_id)
        attributes_map = {}

        for attribute in attributes:
            attr_name = attribute.name.lower()  # Adjust if needed
            attr_value = attribute.code
            variant_name = attribute.variant_type.name

            if attr_name not in attributes_map:
                attributes_map[attr_name] = {
                    'values': [],
                    'variant_name': variant_name
                }

            if attr_value not in attributes_map[attr_name]['values']:
                attributes_map[attr_name]['values'].append(attr_value)

        # Ensure attributes are returned in the correct format
        return JsonResponse({'attributes': attributes_map})
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        return render_error_page(request, error_message, status_code=400)

def generate_combinations(request):
    if request.method == 'POST':
        try:
            # Load the data directly from the request body
            data = json.loads(request.body)
            print("Received Data:", data)
            
            # Ensure data is in the correct format
            if not isinstance(data, dict):
                return JsonResponse({'error': 'Invalid data format'}, status=400)
            
            # Extract attribute names and values
            attribute_names = list(data.keys())
            attribute_values = [data[name] for name in attribute_names]

            # Generate combinations using Cartesian product
            combinations = []
            for combination in product(*attribute_values):
                combination_str = ', '.join(f'{attribute_names[i]}: {combination[i]}' for i in range(len(attribute_names)))
                combinations.append(combination_str)

            return JsonResponse({'combinations': combinations})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def save_combination(request):
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            combination = request.POST.get('combination')
            product_max_price = request.POST.get('product_max_price')
            product_discount_price = request.POST.get('product_discount_price')
            stock = request.POST.get('stock')

            main_product_obj = get_object_or_404(Products, id=int(product_id))
            combination_dict = dict(item.split(": ") for item in combination.split(", "))

            # Create or update VariantProduct
            variant_product, created = VariantProduct.objects.get_or_create(
                product=main_product_obj,
                variant_combination=combination_dict,
                defaults={
                    'product_max_price': product_max_price,
                    'product_discount_price': product_discount_price,
                    'stock': stock,
                    'is_visible': True
                }
            )

            if not created:
                variant_product.product_max_price = product_max_price
                variant_product.product_discount_price = product_discount_price
                variant_product.stock = stock
                variant_product.save()

            # Handle images
            variant_image_gallery, gallery_created = VariantImageGallery.objects.get_or_create(
                variant_product=variant_product
            )

            # Process images
            remove_images = request.POST.getlist('remove_images')
            new_uploaded_images = request.FILES.getlist('new_images')

            current_images = variant_image_gallery.images or []
            updated_images = [img for img in current_images if img not in remove_images]

            for file in new_uploaded_images:
                file_path = default_storage.save(os.path.join('variant_images', file.name), file)
                updated_images.append(file_path.replace("\\", "/"))

            variant_image_gallery.images = updated_images

            # Process videos
            remove_videos = request.POST.getlist('remove_videos')
            new_uploaded_videos = request.FILES.getlist('new_videos')

            current_videos = variant_image_gallery.video or []
            updated_videos = [video for video in current_videos if video not in remove_videos]

            for file in new_uploaded_videos:
                file_path = default_storage.save(os.path.join('variant_videos', file.name), file)
                updated_videos.append(file_path.replace("\\", "/"))

            variant_image_gallery.video = updated_videos

            variant_image_gallery.save()

            return JsonResponse({'success': True})
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@method_decorator(utils.super_admin_only, name='dispatch')
class ProductEdit(View):
    form_class = forms.ProductForm
    template = app + 'admin/product_edit.html'  # Ensure this path is correct

    def get(self, request, pk):
        product = get_object_or_404(Products, pk=pk)
        form = self.form_class(instance=product)

        context = {
            "form": form,
            "product": product,
        }
        return render(request, self.template, context)

    def post(self, request, pk):
        product = get_object_or_404(Products, pk=pk)
        form = self.form_class(request.POST, request.FILES, instance=product)

        if form.is_valid():
            try:
                # Save the updated product
                product = form.save(commit=False)
                if not product.uid:
                    product.uid = utils.get_rand_number(5)
                product.save()

                # Update the related SimpleProduct object
                simple_product_obj, created = SimpleProduct.objects.get_or_create(product=product)
                simple_product_obj.save()  # Save or update the SimpleProduct object

                messages.success(request, "Product updated successfully.")
                return redirect("product:product_list")

            except Exception as e:
                print("Error updating product:", e)
                messages.error(request, f"Error updating product: {str(e)}")
        else:
            # Handle form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        context = {
            "form": form,
            "product": product,
        }

        return render(request, self.template, context)
    
@method_decorator(utils.super_admin_only, name='dispatch')
class ProductList(View):
    template_name = app + "admin/product_list.html"

    def get(self, request):
        try:
            products = Products.objects.all().order_by('pk')
            paginator = Paginator(products, 20)  # Show 20 products per page
            page = request.GET.get('page', 1)
            paginated_products = paginator.page(page)
        except PageNotAnInteger:
            paginated_products = paginator.page(1)
        except EmptyPage:
            paginated_products = paginator.page(paginator.num_pages)
        except Exception as e:
            error_message = f"An error occurred while loading the products: {str(e)}"
            return render_error_page(request, error_message)

        context = {'products': paginated_products}
        return render(request, self.template_name, context)


@method_decorator(utils.super_admin_only, name='dispatch')
class SimpleProductUpdate(View):
    form_class = forms.SimpleProductForm
    template = app + "admin/simple_product_update.html"

    def get(self, request, pk):
        try:
            product = get_object_or_404(SimpleProduct, pk=pk)
            form = self.form_class(instance=product)
            product_images_videos, created = ImageGallery.objects.get_or_create(simple_product=product)
            images = product_images_videos.images or []
            videos = product_images_videos.video or []
        except Exception as e:
            error_message = f"An error occurred while retrieving the product: {str(e)}"
            return render_error_page(request, error_message)

        context = {"form": form, "product": product, "images": images, "videos": videos}
        return render(request, self.template, context)

    def post(self, request, pk):
        try:
            product = get_object_or_404(SimpleProduct, pk=pk)
            form = self.form_class(request.POST, request.FILES, instance=product)
            product_images_videos, created = ImageGallery.objects.get_or_create(simple_product=product)

            if form.is_valid():
                product = form.save(commit=False)

                remove_images = request.POST.getlist('remove_images')
                new_uploaded_images = request.FILES.getlist('new_images')

                current_images = list(product_images_videos.images or [])
                updated_images = [img for img in current_images if img not in remove_images]

                for file in new_uploaded_images:
                    file_path = default_storage.save(os.path.join('product_images', file.name), file)
                    updated_images.append(file_path.replace("\\", "/"))

                if not updated_images:
                    messages.error(request, "At least one image is required.")
                    return self.render_update_form(request, form, product, updated_images, product_images_videos.video)

                product_images_videos.images = updated_images

                remove_videos = request.POST.getlist('remove_videos')
                new_uploaded_videos = request.FILES.getlist('new_videos')

                current_videos = list(product_images_videos.video or [])
                updated_videos = [video for video in current_videos if video not in remove_videos]

                for file in new_uploaded_videos:
                    file_path = default_storage.save(os.path.join('product_videos', file.name), file)
                    updated_videos.append(file_path.replace("\\", "/"))

                product_images_videos.video = updated_videos

                product.is_visible = True
                product.save()
                product_images_videos.save()

                messages.success(request, "Product updated successfully.")
                return redirect("product:simple_product_list")
        except Exception as e:
            error_message = f"An error occurred while updating the product: {str(e)}"
            return render_error_page(request, error_message)

        return self.render_update_form(request, form, product, product_images_videos.images, product_images_videos.video)

    def render_update_form(self, request, form, product, images, videos):
        context = {"form": form, "product": product, "images": images, "videos": videos}
        return render(request, self.template, context)


@method_decorator(utils.super_admin_only, name='dispatch')
class SimpleProductDelete(View):
    def get(self, request, pk):
        try:
            simple_product = get_object_or_404(SimpleProduct, pk=pk)
            product = simple_product.product  # Get the parent product

            simple_product.delete()
            messages.success(request, "Simple product deleted successfully.")
            
            remaining_simple_products = SimpleProduct.objects.filter(product=product).exists()
            if not remaining_simple_products:
                product.delete()
                messages.success(request, "Parent product deleted successfully.")
        except Exception as e:
            error_message = f"An error occurred while deleting the product: {str(e)}"
            return render_error_page(request, error_message)

        return redirect("product:simple_product_list")


class DeliverySettingsUpdateView(View):
    form_class = forms.DeliverySettingsForm
    template_name = app + "admin/delivery_setting.html"

    def get(self, request):
        try:
            delivery_settings = DeliverySettings.objects.first()
            form = self.form_class(instance=delivery_settings)
        except Exception as e:
            error_message = f"An error occurred while retrieving the delivery settings: {str(e)}"
            return render_error_page(request, error_message)

        context = {'form': form}
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            delivery_settings = DeliverySettings.objects.first()
            form = self.form_class(request.POST, instance=delivery_settings)

            if form.is_valid():
                form.save()
                messages.success(request, "Delivery settings updated successfully.")
                return redirect('users:admin_dashboard')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        except Exception as e:
            error_message = f"An error occurred while updating the delivery settings: {str(e)}"
            return render_error_page(request, error_message)

        context = {'form': form}
        return render(request, self.template_name, context)

@method_decorator(utils.super_admin_only, name='dispatch')
class AdminReviewManagementView(View):
    template_name = app + 'admin/admin_review_management.html'
    paginate_by = 20  # Set the number of reviews per page

    def get(self, request):
        try:
            user = request.user
            category_obj = Category.objects.all()

            reviews = ProductReview.objects.select_related('user').order_by('-id')

            # Django's built-in paginator
            paginator = Paginator(reviews, self.paginate_by)
            page_number = request.GET.get('page')
            try:
                paginated_reviews = paginator.page(page_number)
            except PageNotAnInteger:
                paginated_reviews = paginator.page(1)
            except EmptyPage:
                paginated_reviews = paginator.page(paginator.num_pages)

            context = {
                'user': user,
                'category_obj': category_obj,
                'reviews': paginated_reviews,  # Paginated reviews
                'page_obj': paginated_reviews,  # Page object for pagination controls
                'star_range': range(1, 6),  # Star range for rendering star ratings
                'MEDIA_URL': settings.MEDIA_URL,
            }

            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

    def post(self, request, p_id):
        try:
            review_ids = request.POST.getlist('reviews')

            if not review_ids:
                messages.warning(request, "No reviews selected.")
                return redirect('product:admin_review_management')

            # Delete selected reviews
            ProductReview.objects.filter(id__in=review_ids).delete()
            messages.success(request, "Selected reviews have been deleted.")

            return redirect('product:admin_review_management')

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
        
@method_decorator(utils.super_admin_only, name='dispatch')
class ProductSearch(View):
    model = Products
    form_class = forms.ProductForm
    template = app + "admin/product_list.html"

    def post(self, request):
        try:
            filter_by = request.POST.get("filter_by")
            query = request.POST.get("query")

            if filter_by == "pk":
                product_list = self.model.objects.filter(pk=query)
            else:
                product_list = self.model.objects.filter(name__icontains=query)

            paginated_data = utils.paginate(request, product_list, 10)

            context = {
                "form": self.form_class,
                "products": product_list,
                "data_list": paginated_data,
                "MEDIA_URL": settings.MEDIA_URL
            }
            return render(request, self.template, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
@method_decorator(utils.super_admin_only, name='dispatch')
class ProductSearch(View):
    model = Products
    form_class = forms.ProductForm
    template = app + "admin/product_list.html"

    def post(self, request):
        try:
            filter_by = request.POST.get("filter_by")
            query = request.POST.get("query")

            if filter_by == "pk":
                product_list = self.model.objects.filter(pk=query)
            else:
                product_list = self.model.objects.filter(name__icontains=query)

            paginated_data = utils.paginate(request, product_list, 10)

            context = {
                "form": self.form_class,
                "products": product_list,
                "data_list": paginated_data,
                "MEDIA_URL": settings.MEDIA_URL
            }
            return render(request, self.template, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class ProductFilter(View):
    model = Products
    template = app + "admin/product_list.html"

    def get(self, request):
        try:
            filter_by = request.GET.get("filter_by")
            if filter_by == "trending":
                product_list = self.model.objects.filter(trending="yes").order_by('-id')
            elif filter_by == "show_as_new":
                product_list = self.model.objects.filter(show_as_new="yes").order_by('-id')
            elif filter_by == "display_as_bestseller":
                product_list = self.model.objects.filter(display_as_bestseller="yes").order_by('-id')
            elif filter_by == "hide":
                product_list = self.model.objects.filter(hide="yes").order_by('-id')
            else:
                product_list = self.model.objects.filter().order_by('-id')

            paginated_data = utils.paginate(request, product_list, 50)

            context = {
                "product_list": product_list,
                "data_list": paginated_data,
                "MEDIA_URL": settings.MEDIA_URL
            }
            return render(request, self.template, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class SimpleProductList(View):
    template_name = app + "admin/simple_product_list.html"

    def get(self, request):
        try:
            products = SimpleProduct.objects.all()

            paginator = Paginator(products, 10)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            context = {
                'page_obj': page_obj
            }
            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)

@method_decorator(utils.super_admin_only, name='dispatch')
class SimpleProductSearch(View):
    model = SimpleProduct
    form_class = forms.SimpleProductForm
    template = app + "admin/simple_product_list.html"

    def post(self, request):
        try:
            filter_by = request.POST.get("filter_by")
            query = request.POST.get("query")

            if filter_by == "pk":
                simple_product_list = self.model.objects.filter(pk=query)
            else:
                product_list = Products.objects.filter(name__icontains=query)
                simple_product_list = self.model.objects.filter(product__in=product_list)

            paginated_data = utils.paginate(request, simple_product_list, 10)

            context = {
                "form": self.form_class,
                "products": simple_product_list,
                "data_list": paginated_data,
                "MEDIA_URL": settings.MEDIA_URL
            }
            return render(request, self.template, context)

        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            return render_error_page(request, error_message, status_code=400)
