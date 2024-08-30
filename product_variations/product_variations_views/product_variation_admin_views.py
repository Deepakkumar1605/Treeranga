import os
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from helpers import utils

from product.models import ImageGallery, Products
from product_variations import forms
from product_variations.models import Attribute, Variant, VariantProduct
from django.core.files.storage import default_storage

app = "product_variations/"



@method_decorator(utils.super_admin_only, name='dispatch')
class VariationList(View):
    model = Variant
    template = app + "admin/variation_list.html"
    form_class = forms.VariantForm
    def get(self, request):
        variant_list = self.model.objects.all().order_by('-id')
        context = {
            "form": self.form_class,
            "variant_list":variant_list,
        }
        return render(request, self.template, context)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, f"{request.POST['name']} is added to the list.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect("product_variations:variation_list")

@method_decorator(utils.super_admin_only, name='dispatch')
class VariantionAdd(View):
    model = Variant
    form_class = forms.VariantForm
    template = app + "admin/variation_add.html"

    def get(self, request):
        variant_list = self.model.objects.all().order_by('-id')
        context = {
            "variant_list": variant_list,
            "form": self.form_class,
        }
        return render(request, self.template, context)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"Variant added successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect("product_variations:variation_list")

@method_decorator(utils.super_admin_only, name='dispatch')
class VariationUpdate(View):
    model = Variant
    form_class = forms.VariantForm
    template = app + "admin/variation_update.html"  # Adjust template path as needed

    def get(self, request, variation_id):
        variation = get_object_or_404(self.model, id=variation_id)
        form = self.form_class(instance=variation)
        return render(request, self.template, {'form': form})

    def post(self, request, variation_id):
        variation = get_object_or_404(self.model, id=variation_id)
        form = self.form_class(request.POST, request.FILES, instance=variation)
        if form.is_valid():
            form.save()
            messages.success(request, f"{variation.name} updated successfully.")
            return redirect("product_variations:variation_list")  # Removed variation_id argument
        else:
            messages.error(request, "Form is not valid. Please check the errors.")
            return render(request, self.template, {'form': form})


@method_decorator(utils.super_admin_only, name='dispatch')
class VariationDelete(View):
    model = Variant
    form_class = forms.VariantForm
    template = app + "admin/variation_update.html"

    def get(self,request, variation_id):
        variation = self.model.objects.get(id= variation_id).delete()
        messages.info(request, "variation is deleted successfully....")
        return redirect("product_variations:variation_list")

@method_decorator(utils.super_admin_only, name='dispatch')
class AttributeList(View):
    model = Attribute
    template = app + "admin/attribute_list.html"
    form_class = forms.AttributeForm

    def get(self, request):
        attribute_list = self.model.objects.all().order_by('-id')
        context = {
            "form": self.form_class(),
            "attribute_list": attribute_list,
        }
        return render(request, self.template, context)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, f"Attribute {request.POST['name']} is added to the list.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect("product_variations:attribute_list")
    
@method_decorator(utils.super_admin_only, name='dispatch')
class AttributeAdd(View):
    model = Attribute
    form_class = forms.AttributeForm
    template = app + "admin/attribute_add.html"

    def get(self, request):
        attribute_list = self.model.objects.all().order_by('-id')
        context = {
            "attribute_list": attribute_list,
            "form": self.form_class(),
        }
        return render(request, self.template, context)

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"Attribute {request.POST['name']} added successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')

        return redirect("product_variations:attribute_list")
    
@method_decorator(utils.super_admin_only, name='dispatch')
class AttributeUpdate(View):
    model = Attribute
    form_class = forms.AttributeForm
    template = app + "admin/attribute_update.html"  # Adjust template path as needed

    def get(self, request, attribute_id):
        attribute = get_object_or_404(self.model, id=attribute_id)
        form = self.form_class(instance=attribute)
        return render(request, self.template, {'form': form})

    def post(self, request, attribute_id):
        attribute = get_object_or_404(self.model, id=attribute_id)
        form = self.form_class(request.POST, request.FILES, instance=attribute)
        if form.is_valid():
            form.save()
            messages.success(request, f"Attribute {attribute.name} updated successfully.")
            return redirect("product_variations:attribute_list")
        else:
            messages.error(request, "Form is not valid. Please check the errors.")
            return render(request, self.template, {'form': form})
        
@method_decorator(utils.super_admin_only, name='dispatch')
class AttributeDelete(View):
    model = Attribute

    def get(self, request, attribute_id):
        attribute = get_object_or_404(self.model, id=attribute_id)
        attribute.delete()
        messages.info(request, f"Attribute {attribute.name} deleted successfully.")
        return redirect("product_variations:attribute_list")
    


@method_decorator(utils.super_admin_only, name='dispatch')
class VariantProductList(View):
    template_name = app + "admin/variant_product_list.html"

    def get(self, request):
        variant_products = VariantProduct.objects.all()

        context = {
            'variant_products': variant_products,
        }
        return render(request, self.template_name, context)
    
@method_decorator(utils.super_admin_only, name='dispatch')
class VariantProductUpdate(View):
    form_class = forms.ProductVariantForm
    template = app + "admin/variant_product_update.html"

    def get(self, request, pk):
        variant_product = get_object_or_404(VariantProduct, pk=pk)
        form = self.form_class(instance=variant_product)
        
        # Fetch the ImageGallery instance for the variant product
        product_images_videos, created = ImageGallery.objects.get_or_create(variant_product=variant_product)

        # Ensure images and videos are fetched correctly as lists
        images = product_images_videos.images if product_images_videos.images else []
        videos = product_images_videos.video if product_images_videos.video else []

        context = {
            "form": form,
            "variant_product": variant_product,
            "images": images,  # Pass images to the template
            "videos": videos    # Pass videos to the template
        }
        return render(request, self.template, context)



    def post(self, request, pk):
        variant_product = get_object_or_404(VariantProduct, pk=pk)
        form = self.form_class(request.POST, request.FILES, instance=variant_product)
        product_images_videos, created = ImageGallery.objects.get_or_create(variant_product=variant_product)

        if form.is_valid():
            try:
                variant_product = form.save(commit=False)

                # Handle image updates
                remove_images = request.POST.getlist('remove_images')
                new_uploaded_images = request.FILES.getlist('new_images')

                current_images = list(product_images_videos.images) if product_images_videos.images else []
                updated_images = [img for img in current_images if img not in remove_images]

                for file in new_uploaded_images:
                    file_path = default_storage.save(os.path.join('product_images', file.name), file)
                    updated_images.append(file_path.replace("\\", "/"))

                product_images_videos.images = updated_images

                # Handle video updates
                remove_videos = request.POST.getlist('remove_videos')
                new_uploaded_videos = request.FILES.getlist('new_videos')

                current_videos = list(product_images_videos.video) if product_images_videos.video else []
                updated_videos = [video for video in current_videos if video not in remove_videos]

                for file in new_uploaded_videos:
                    file_path = default_storage.save(os.path.join('product_videos', file.name), file)
                    updated_videos.append(file_path.replace("\\", "/"))

                product_images_videos.video = updated_videos 

                variant_product.save()
                product_images_videos.save()
                messages.success(request, "Variant product updated successfully.")
                return redirect("product_variations:variant_product_list")

            except Exception as e:
                print("Error updating variant product:", e)
                messages.error(request, f"Error updating variant product: {str(e)}")

        context = {
            "form": form,
            "variant_product": variant_product
        }
        return render(request, self.template, context)

@method_decorator(utils.super_admin_only, name='dispatch')
class VariantProductDelete(View):

    def get(self, request, pk):
        variant_product = get_object_or_404(VariantProduct, pk=pk)
        parent_product = variant_product.product  

        try:
            variant_product.delete()
            messages.success(request, "Variant product deleted successfully.")
            
            remaining_variant_products = VariantProduct.objects.filter(product=parent_product).exists()
            if not remaining_variant_products:
                parent_product.delete()
                messages.success(request, "Parent product deleted successfully.")
                
        except Exception as e:
            print("Error deleting variant product:", e)
            messages.error(request, f"Error deleting variant product: {str(e)}")

        return redirect("product_variations:variant_product_list")