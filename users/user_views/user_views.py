from django.shortcuts import render, redirect
from datetime import datetime
from django.conf import settings
from django.views import View
from django.contrib import messages
from users import forms
from users.models import User
from uuid import uuid4
from product.models import Category
app = "users/user/"

class ProfileView(View):
    template = app + "userprofile.html"

    def get(self, request):
        user = request.user
        category_obj = Category.objects.all()

        if not user.is_authenticated:
            return redirect("users:login")

        return render(request, self.template, locals())


class UpdateProfileView(View):
    template = app + "update_profile.html"
    form = forms.UpdateProfileForm

    def get(self, request):
        user = request.user
        
        initial_data = {
            "full_name": user.full_name,
            "email": user.email,
            "contact": user.contact,

        }
        form = self.form(initial=initial_data)

        return render(request, self.template, locals())

    def post(self, request):
        form = self.form(request.POST, request.FILES)
        
        if form.is_valid():
            email = form.cleaned_data["email"]
            full_name = form.cleaned_data["full_name"]
            contact = form.cleaned_data["contact"]
            profile_picture = form.cleaned_data["profile_pic"]
            user = request.user

            try:
                user.email = email
                user.full_name = full_name
                user.contact = contact

                if profile_picture:
                    user.profile_pic = profile_picture

                user.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("users:account_details")

            except Exception as e:
                messages.error(request, f"Error in updating profile: {str(e)}")

        return render(request, self.template, {'form': form})





class AllAddress(View):
    template = app + "alladdress.html"

    def get(self, request):
        user = request.user
        addresses = user.address or []  # This will return a list of addresses

        return render(request, self.template, {"addresses": addresses})



class ProfileAddAddress(View):
    template = app + "addaddress.html"
    form = forms.AddressForm

    def get(self, request):
        form = self.form()
        return render(request, self.template, locals())

    def post(self, request):
        form = self.form(request.POST)
        if form.is_valid():
            Address1 = form.cleaned_data["Address1"]
            Address2 = form.cleaned_data["Address2"]
            country = form.cleaned_data["country"]
            state = form.cleaned_data["state"]
            city = form.cleaned_data["city"]
            mobile_no = form.cleaned_data["mobile_no"]
            pincode = form.cleaned_data["pincode"]

            address_id = str(uuid4())

            address_data = {
                "id": address_id,
                "Address1": Address1,
                "Address2": Address2,
                "country": country,
                "state": state,
                "city": city,
                'mobile_no':mobile_no,
                "pincode": pincode,
            }

            user = request.user
            addresses = user.address or []

            # Append the new address data to the list of addresses
            addresses.append(address_data)

            # Save the updated list of addresses back to the user model
            user.address = addresses
            user.save()

            return redirect("users:alladdress")
        else:
            return redirect("users:addaddress")

class ProfileUpdateAddress(View):
    template = app + "update_address.html"
    form = forms.AddressForm

    def get(self, request, address_id):
        user = request.user
        addresses = user.address or []
        address = next((addr for addr in addresses if addr["id"] == address_id), None)
        
        if not address:
            messages.error(request, "Address not found.")
            return redirect("users:alladdress")

        form = self.form(initial=address)
        return render(request, self.template, {'form': form, 'address_id': address_id})

    def post(self, request, address_id):
        form = self.form(request.POST)
        if form.is_valid():
            user = request.user
            addresses = user.address or []

            # Find the existing address
            address_index = next((index for (index, addr) in enumerate(addresses) if addr["id"] == address_id), None)

            if address_index is None:
                messages.error(request, "Address not found.")
                return redirect("users:alladdress")

            address_data = {
                "id": address_id,
                "Address1": form.cleaned_data["Address1"],
                "Address2": form.cleaned_data["Address2"],
                "country": form.cleaned_data["country"],
                "state": form.cleaned_data["state"],
                "city": form.cleaned_data["city"],
                "mobile_no": form.cleaned_data["contact"],
                "pincode": form.cleaned_data["pincode"],
            }

            # Update the address in the list
            addresses[address_index] = address_data

            # Save the updated list of addresses back to the user model
            user.address = addresses
            user.save()

            messages.success(request, "Address updated successfully.")
            return redirect("users:alladdress")
        else:
            messages.error(request, "Invalid address form. Please correct the errors below.")
            return render(request, self.template, {'form': form, 'address_id': address_id})
        
class ProfileDeleteAddress(View):
    def get(self, request, address_id):
        user = request.user
        addresses = user.address or []

        # Filter out the address with the specified ID
        addresses = [
            address for address in addresses if address.get("id") != address_id
        ]

        # Update the user model with the modified list of addresses
        user.address = addresses
        user.save()

        return redirect("users:alladdress")


class AccountDetails(View):
    template = app + "account_details.html"

    def get(self, request):
        user = request.user

        if not user.is_authenticated:
            return redirect("users:login")

        category_obj = Category.objects.all()

        return render(request, self.template, {
            'userobj': user,
            'category_obj': category_obj
        })
