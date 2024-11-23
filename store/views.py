from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import json
import datetime
from django.db.models import Q
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm, CustomerForm
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

def store(request):
	data = cartData(request)
	cartItems = data['cartItems']
	
	# Start with all products
	products = Product.objects.filter(is_available=True)
	
	# Get all filter parameters
	filters = {}
	category_slug = request.GET.get('category')
	brand = request.GET.get('brand')
	min_price = request.GET.get('min_price')
	max_price = request.GET.get('max_price')
	sort_by = request.GET.get('sort')
	
	# Apply category filter
	if category_slug:
		filters['category'] = category_slug
		try:
			category = Category.objects.get(slug=category_slug)
			if category.is_department:
				subcategories = Category.objects.filter(parent=category)
				products = products.filter(category__in=subcategories)
			else:
				products = products.filter(category=category)
		except Category.DoesNotExist:
			pass
	
	# Apply brand filter
	if brand:
		filters['brand'] = brand
		products = products.filter(brand=brand)
	
	# Apply price filters
	if min_price:
		try:
			filters['min_price'] = min_price
			products = products.filter(price__gte=float(min_price))
		except ValueError:
			pass
	
	if max_price:
		try:
			filters['max_price'] = max_price
			products = products.filter(price__lte=float(max_price))
		except ValueError:
			pass
	
	# Apply sorting
	if sort_by:
		filters['sort'] = sort_by
		if sort_by == 'price_asc':
			products = products.order_by('price')
		elif sort_by == 'price_desc':
			products = products.order_by('-price')
	
	# Get all categories for the sidebar
	main_categories = Category.objects.filter(is_department=True)
	subcategories = Category.objects.filter(is_department=False)
	
	# Get all unique brands
	brands = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
	
	# Debug print categories
	print("\nMain Categories:")
	for cat in main_categories:
		print(f"- {cat.name} (slug: {cat.slug})")
	
	print("\nSubcategories:")
	for cat in subcategories:
		print(f"- {cat.name} (slug: {cat.slug}, parent: {cat.parent})")
	
	context = {
		'products': products,
		'cartItems': cartItems,
		'main_categories': main_categories,
		'subcategories': subcategories,
		'brands': brands,
		'active_filters': filters,
		'current_category': category_slug,
		'current_brand': brand,
	}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

@login_required(login_url='login_register_choice')
def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	# Check if any items are out of stock
	for item in items:
		if item.product.stock < item.quantity:
			messages.error(request, f'Sorry, {item.product.name} only has {item.product.stock} units available.')
			return redirect('cart')

	context = {
		'items': items,
		'order': order,
		'cartItems': cartItems,
		'paypal_client_id': settings.PAYPAL_CLIENT_ID,
	}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	if request.method == 'POST':
		try:
			data = json.loads(request.body)
			form_data = data['form']
			
			customer = request.user.customer
			order = Order.objects.get(customer=customer, complete=False)
			total = float(form_data['total'])
			order.transaction_id = form_data['transaction_id']
			
			# Verify order total matches cart total
			if total == float(order.get_cart_total):
				# Update stock levels
				order_items = order.orderitem_set.all()
				for item in order_items:
					product = item.product
					product.stock -= item.quantity
					product.save()
				
				# Complete the order
				order.complete = True
				order.transaction_id = form_data['transaction_id']
				order.save()
				
				# Create shipping address
				ShippingAddress.objects.create(
					customer=customer,
					order=order,
					address=form_data['address'],
					city=form_data['city'],
					state=form_data['state'],
					zipcode=form_data['zipcode'],
				)
				
				return JsonResponse({
					'success': True,
					'redirect_url': reverse('order_success', kwargs={'order_id': order.id})
				})
			
			return JsonResponse({'error': 'Total price mismatch'}, status=400)
			
		except Exception as e:
			return JsonResponse({'error': str(e)}, status=400)
	return JsonResponse('Invalid request', status=400)

def product_detail(request, product_id):
	data = cartData(request)
	cartItems = data['cartItems']
	
	product = get_object_or_404(Product, id=product_id)
	
	# Get related products from the same category
	related_products = Product.objects.filter(
		category=product.category
	).exclude(id=product.id)[:4]
	
	context = {
		'product': product,
		'cartItems': cartItems,
		'related_products': related_products,
	}
	return render(request, 'store/product_detail.html', context)

def register_user(request):
	if request.method == 'POST':
		form = CustomUserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			# Create customer profile
			Customer.objects.create(
				user=user,
				name=user.username,
				email=user.email
			)
			login(request, user)
			return redirect('checkout')
	else:
		form = CustomUserCreationForm()
	return render(request, 'store/register.html', {'form': form})

def login_view(request):
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect('checkout')
	return render(request, 'store/login.html')

@csrf_exempt
def process_order(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['total'])
	order.transaction_id = transaction_id

	if total == float(order.get_cart_total):
		order.complete = True
	order.save()

	if order.shipping:
		ShippingAddress.objects.create(
			customer=customer,
			order=order,
			address=data['shipping']['address'],
			city=data['shipping']['city'],
			state=data['shipping']['state'],
			zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment complete!', safe=False)

def login_register_choice(request):
	"""View to let users choose between login, register, or guest checkout"""
	# If user is already authenticated, redirect to checkout
	if request.user.is_authenticated:
		return redirect('checkout')
		
	return render(request, 'store/login_register_choice.html')

@login_required
def orderSuccess(request, order_id):
    try:
        order = Order.objects.get(id=order_id, customer=request.user.customer, complete=True)
    except Order.DoesNotExist:
        return redirect('store')
        
    context = {
        'order': order
    }
    return render(request, 'store/order_success.html', context)
