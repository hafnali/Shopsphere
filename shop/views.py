from django.shortcuts import render

from rest_framework.response import Response

from rest_framework import status

from rest_framework.generics import CreateAPIView,ListAPIView,RetrieveAPIView,UpdateAPIView,DestroyAPIView

from rest_framework import authentication,permissions

from shop.serializers import UserSerializer,ProductSerializer,BasketSerializer,BasketItemSerializer,OrderSerializer

from rest_framework.views import APIView

from django.contrib.auth.models import User

from shop.models import Product,Size,BasketItem,Order

import razorpay

# Create your views here.


KEY_ID="rzp_test_IugV9EbcoTvGBR"
KEY_SECRET="Wu57wXp2X2xu31QPUrIqCQSV"

class SighUpView(CreateAPIView):

    serializer_class=UserSerializer

    queryset=User.objects.all()

class ProductListView(ListAPIView):

    serializer_class=ProductSerializer

    queryset=Product.objects.all()

    
    authentication_classes=[authentication.TokenAuthentication]

    permission_classes=[permissions.IsAuthenticated]

class ProductDetailView(RetrieveAPIView):

    serializer_class=ProductSerializer

    queryset=Product.objects.all()

    authentication_classes=[authentication.TokenAuthentication]

    permission_classes=[permissions.IsAuthenticated]

    # def add_to_cart(self,request,*args,**kwargs):

    #     return Response(data={"message":"custom method"})


class AddToCartView(APIView):

    authentication_classes=[authentication.TokenAuthentication]

    permission_classes=[permissions.IsAuthenticated]

    def post(Self,request,*args,**kwargs):

        basket_obj=request.user.cart

        id=kwargs.get("pk")

        product_obj=Product.objects.get(id=id)

        size_name=request.data.get("size")

        size_obj=Size.objects.get(name=size_name)

        quantity=request.data.get("quantity")

        BasketItem.objects.create(
            basket_object=basket_obj,
            product_object=product_obj,
            size_object=size_obj,
            quantity=quantity

        )

        return Response(data={"message":"created"})


class CartListView(APIView):

    authentication_classes=[authentication.TokenAuthentication]

    permission_classes=[permissions.IsAuthenticated]

    def get(Self,request,*args,**kwargs):

        qs=request.user.cart

        serializer_instance=BasketSerializer(qs)

        return Response(data=serializer_instance.data)


class CartItemUpdateView(UpdateAPIView,DestroyAPIView):

    authentication_classes=[authentication.TokenAuthentication]

    permission_classe=[permissions.IsAuthenticated]

    serializer_class=BasketItemSerializer

    queryset=BasketItem.objects.all()

    def perform_update(self,serializer):

        size_name=self.request.data.get("size_object")  

        size_obj=Size.objects.get(name=size_name)

        serializer.save(size_object=size_obj)

    

class CheckOutView(APIView):

    authentication_classes=[authentication.TokenAuthentication]

    permission_classes=[permissions.IsAuthenticated]

    def post(self,request,*args,**kwargs):

        user_obj=request.user

        delivery_address=request.data.get("delivery_address")

        phone=request.data.get("phone")

        pin=request.data.get("pin")

        email=request.data.get("email")

        payment_mode=request.data.get("payment_mode")

        order_instance=Order.objects.create(
            user_object=user_obj,
            delivery_address=delivery_address,
            phone=phone,
            pin=pin,
            email=email,
            payment_mode=payment_mode
        )
        # cart_items=request.user.cartitems.filter(is_order_placed=False)
        cart_items=request.user.cart.basketitems

        for bi in cart_items:
            # bi is a basket item object

            order_instance.basket_item_objects.add(bi)

            bi.is_order_placed=True

            bi.save()
        if payment_mode=="cod":
            order_instance.save()

            return Response(data={"message":"created"})
        
        elif payment_mode=="online" and order_instance:

            client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

            data = { "amount": order_instance.order_total*100, "currency": "INR", "receipt": "order_rcptid_11" }

            payment = client.order.create(data=data)

            print(payment)

            order_id=payment.get("id")

            key_id=KEY_ID

            order_total=payment.get("amount")

            user=request.user.username

            data={
                "order_id":order_id,
                "key_id":key_id,
                "order_total":order_total,
                "user":user,
                "phone":phone
            }

            order_instance.order_id=order_id

            order_instance.save()

            return Response(data=data,status=status.HTTP_201_CREATED)
        
class OrderSummaryView(ListAPIView):

    authentication_classes=[authentication.TokenAuthentication]

    permission_classes=[permissions.IsAuthenticated]

    serializer_class=OrderSerializer

    queryset=Order.objects.all()

class PaymentVerificationView(APIView):
    
    def post(self,request,*args,**kwargs):
        # print(request.POST)
        data=request.POST

        client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
        
        try:

            client.utility.verify_payment_signature(data)
            # print('payment success')
        
            order_id=data.get('razorpay_order_id')
        
            order_object=Order.objects.get(order_id=order_id)
        
            order_object.is_paid=True
        
            order_object.save()
        
            return Response(data={'message':"payment success"},status=status.HTTP_200_OK)
        
        except:
        
           return Response(data={'message':"payment error"},status=status.HTTP_400_BAD_REQUEST)


    










