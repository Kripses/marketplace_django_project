from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    CreateView,
    DetailView,
    TemplateView,
    UpdateView,
)

from .forms import UserRegistrationForm, ProfileForm
from .models import BrowsingHistory, Profile, Seller
from adminsettings.models import SiteSettings
from cart.models import Order
from products.models import Product

from cart.services.cart_actions import merge_cart_products


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    login_url = 'account:login'
    model = Profile
    form_class = ProfileForm
    template_name = 'registration/profile.jinja2'
    success_url = reverse_lazy('account:profile')

    def form_valid(self, form):
        form.save()
        response = super().form_valid(form)

        if form.cleaned_data['new_password1'] != form.cleaned_data['new_password2']:
            messages.error(self.request, 'Пароли не совпадают.')
            return self.render_to_response(self.get_context_data(form=form))

        username = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        messages.success(self.request, "Данные успешно обновлены.")
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(self.request, "Ошибка обновления данных.")
        return response

    def get_object(self, queryset=None):
        return self.request.user


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'registration/registr.jinja2'
    success_url = reverse_lazy('account:account')

    def form_valid(self, form):
        # form.save()
        user_profile = form.save(commit=False)
        full_name = form.cleaned_data.get('full_name')
        # = input_string.split()
        full_name = full_name.split()
        user_profile.username = full_name[0]
        if len(full_name) > 1:
            user_profile.first_name = full_name[1]
        if len(full_name) > 2:
            user_profile.last_name = full_name[2]
        user_profile.save()
        response = super().form_valid(form)

        if form.cleaned_data['password1'] != form.cleaned_data['password2']:
            messages.error(self.request, 'Пароли не совпадают.')
            return self.render_to_response(self.get_context_data(form=form))

        username = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(
            self.request,
            username=username,
            password=password,
        )
        login(request=self.request, user=user)
        return response

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        # print(form)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form})


class UserLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'registration/login.jinja2'

    def post(self, request, *args, **kwargs):
        super(UserLoginView, self).post(self, request, *args, **kwargs)
        user = authenticate(request, email=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            merge_cart_products(user, request.session.get('cart'))
            login(request, user)
            return redirect('account:profile')
        return render(request, 'registration/login.jinja2', context={'errors': 'Неверный логин или пароль'})


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('account:login')


# class UserAccountView(LoginRequiredMixin, TemplateView):
#     login_url = 'account:login'
#     template_name = 'registration/account.jinja2'


class UserEmailView(LoginRequiredMixin, TemplateView):
    login_url = 'account:login'
    template_name = 'registration/e-mail.jinja2'


class SellerDetailView(DetailView):
    template_name = 'users/seller_details.jinja2'
    model = Seller
    context_object_name = 'seller'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['products'] = Product.objects.filter(sellers=kwargs['object']).order_by('-count_sells')
        context['top_products_cache_time'] = (
            SiteSettings.objects.values('top_product_cache_time')[0]['top_product_cache_time']
        )

        return context


class HistoryOrderView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/historyorder.jinja2'
    login_url = 'account:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history = Order.objects.filter(profile=self.request.user.id).order_by('-created_at')[:20]

        context['history'] = history

        return context


class UserAccountView(HistoryOrderView):
    login_url = 'account:login'
    template_name = 'registration/account.jinja2'


class UserBrowsingHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/browsing-history.jinja2'
    login_url = 'account:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        history = BrowsingHistory.objects.filter(profile=self.request.user).order_by('-timestamp')[:20]

        for item in history:
            product = item.product
            first_image = product.images.first()

            item.image_url = first_image.image.url if first_image else None

        context['history'] = history

        return context
