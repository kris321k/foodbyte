from django.shortcuts import render
from .models import Person, Category,FoodItem,otp,Cart,CartItem,Restaurent,order,AditionalFoodItems
from rest_framework.views import APIView
from .serializers import Personserializer,categoryserializer,foodserializer,ReviewSerializer,otpserializer,CartSerializer,CartItemserializer,RestaurentSerializer,OrderSerializer
from rest_framework.response import Response
from django.contrib.auth import authenticate, login as django_login
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets,filters
from .models import Review
import random
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
import stripe


stripe.api_key = settings.STRIPE_TEST_SECRET_KEY




#functions to get the token for the user

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

#view r the signup
class submitData(APIView):
    def post(self, request):
        serialized_data = Personserializer(data=request.data)
        if serialized_data.is_valid():

            serialized_data.save()
            return Response({'registration': 'success'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)
        
#view for the login
class login(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({
                'login': 'failed',
                'message': 'Email and password are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)
        if user:
            tokens = get_tokens_for_user(user)
            return Response({
                'login': 'success',
                'access_token': tokens['access'],  # Access the correct key 'access'
                'refresh_token': tokens['refresh']  # Access the correct key 'refresh'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'login': 'failed',
                'message': 'Invalid email or password.'
            }, status=status.HTTP_401_UNAUTHORIZED)
#view for logout


#view to add aditional details to the profile
class profile(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        serialized_data = Personserializer(user, data=request.data, partial=True)
        if serialized_data.is_valid():
            serialized_data.save()
            user.refresh_from_db()
            return Response({
                'message':'profile updated succesfully',
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phonenumer,
                'email':user.email,
                'address':user.address
            }, status=status.HTTP_200_OK)

        else:
            return Response(serialized_data.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self,request):
        user=request.user
        serialiazeddata=Personserializer(user)
        user.refresh_from_db()
        return Response({
            'data':serialiazeddata.data
        },status=status.HTTP_200_OK)

#api for displaying front end homepage

class home(APIView):

    permission_classes = [AllowAny]



    def get(self,request):
        catergories=Category.objects.all()
        catergoryserializedata=categoryserializer(catergories, many=True)

        #code to popular food items
        Popularfooditems=[]
        fooditems=FoodItem.objects.all()

        for fooditem in fooditems:
            fooditemserialized=foodserializer(fooditem)
            Popularfooditems.append(fooditemserialized.data)


        return Response({
            'categories':catergoryserializedata.data,
            'popularitems':Popularfooditems
        },status=status.HTTP_200_OK)


class displayCategories(APIView):
    #permission_classes=[IsAuthenticated]
    def get(self,request,category_name):
        category=Category.objects.filter(category_name=category_name).first()
        Categoryfooditems=FoodItem.objects.filter(category=category)
        Categoryfooditemsserializedata=foodserializer(Categoryfooditems, many=True)
        return Response({
            'categoryfooditems':Categoryfooditemsserializedata.data
        })


class review(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request,item_name):
        try:
            user = request.user
            food_item = FoodItem.objects.filter(item_name = item_name).first()
            review_text = request.data['review_text']

            reviewObj = Review(person = user, food_item = food_item, review_text = review_text)
            reviewObj.save()
            return Response({
                'status':'success'
            },status = status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error':e
            } )
        


    def get(self,request,item_name):
        user=request.user
        food_item=FoodItem.objects.get(item_name=item_name)
        if Review.objects.filter(food_item=food_item).exists():
            review=Review.objects.filter(food_item=food_item)
            ReviewData = []
            for Data in review:
                ReviewData.append({
                    'review_text':Data.review_text,
                    'email':Data.person.email
                })
            return Response({
                'data':ReviewData
            })
        
        else :
            return Response({
                'not exists':True
            }, status = status.HTTP_404_NOT_FOUND)
        

class Reviewpatch(APIView):

    def patch(self,request,item_name,review_id):
        user=request.user
        food_item=FoodItem.objects.get(item_name=item_name)
        review = Review.objects.get(person=user, food_item=food_item,id=review_id)
        serialized_review=ReviewSerializer(review,data=request.data, partial=True)
        if serialized_review.is_valid():
            serialized_review.save()
            return Response({
                'success':'updated successfully'
            }, status=status.HTTP_200_OK)



class ForgotPassword(APIView):
    def post(self,request):
        email=request.data['email']
        if Person.objects.filter(email=request.data['email']).exists():
            person=Person.objects.filter(email=email).first()
            otpn=random.randint(1000,9999)
            opt_num=otp(otp_number=otpn,person=person)
            opt_num.save()
            response = Response({
                'otp': opt_num.otp_number
            })

            subject = 'otp'
            message = f'Your OTP code for password reset is: {opt_num.otp_number}'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email]


            send_mail(subject, message, from_email, recipient_list)
            return Response({
                'success':'otp sent'
            },status=status.HTTP_200_OK)

        else:
            return Response({
                'failure':'person does not exist'
            },status=status.HTTP_404_NOT_FOUND)




class verifyOtp(APIView):
    def post(self,request):
        email=request.COOKIES['email']
        user=Person.objects.filter(email=email).first()
        if user:
            Otp=otp.objects.filter(person=user).last()
            if Otp.otp_number == request.data['otp_num']:
                django_login(request,user)
                return Response({
                    'login':'sucess'
                },status=status.HTTP_200_OK)
            else:
                return Response({
                    'false':'invalid otp'
                },status=status.HTTP_401_UNAUTHORIZED)



class Cartaccess(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request,item_name):
        user=request.user
        #cart, created=Cart.objects.get_or_create(person=user,defaults={'quantity':0,'total_price':0})


        fooditem=FoodItem.objects.filter(item_name=item_name).first()
        if not fooditem:
            return Response({
                'failed':'true'
            },status=status.HTTP_400_BAD_REQUEST)

        cart, created=Cart.objects.get_or_create(person=user)


        cartitem, created1=CartItem.objects.get_or_create(cart=cart,fooditems=fooditem)

        cartitem.quantity+=1
        cartitem.save()
        cartItems=cart.cart_items.all()

        total_price=sum(item.fooditems.item_price*item.quantity for item in cartItems)
        total_quantity=sum(item.quantity for item in cartItems)

        cart.total_price=total_price
        cart.quantity=total_quantity
        cart.save()

        cartitemserialized=CartItemserializer(cartitem)
        cartserialized=CartSerializer(cart)

        return Response({
            'cartitems':cartitemserialized.data,
            'cartdata':cartserialized.data
        },status=status.HTTP_200_OK)


    def get(self,request,item_name=None):
        user=request.user
        cart,created=Cart.objects.get_or_create(person=user)

        if not cart.cart_items.exists():
            return Response({
                'display':'cart empty'
            },status=status.HTTP_200_OK)


        cartitems=cart.cart_items.all()
        cartitemsserialized=CartItemserializer(cartitems, many=True)
        cartserializeddata=CartSerializer(cart)

        food_items_details=[]

        for cartitem in cartitems:
            fooditem=foodserializer(cartitem.fooditems)
            food_items_details.append({
                'items_detailes':fooditem.data,
                'quantity':cartitem.quantity
            })


        new_food_items_details=food_items_details[::-1]


        return Response({
            'cart_items':cartitemsserialized.data,
            'fooditems':new_food_items_details,
            'cart_details':cartserializeddata.data
        },status=status.HTTP_200_OK)


    def delete(self,request,item_name):
        user=request.user
        cart=Cart.objects.filter(person=user).first()

        fooditem=FoodItem.objects.filter(item_name=item_name).first()

        cartitem=CartItem.objects.filter(cart=cart,fooditems=fooditem).first()
        cartitem.delete()

        if not cart.cart_items.exists():
            cart.total_price=0
            cart.quantity=0
            cart.save()
        else:
            cart.total_price=sum(item.fooditems.item_price*item.quantity for item in cart.cart_items.all())
            cart.quantity=sum(item.quantity for item in cart.cart_items.all())
            cart.save()

        return Response({
            'success':'item deleted successfully'
        },status=status.HTTP_200_OK)


class displayCart(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        user=request.user
        cart=Cart.objects.filter(person=user).first()
        if not cart:
            return Response({
                'error':'cart not found with person'
            },status=status.HTTP_404_NOT_FOUND)
        serialized_cart=CartSerializer(cart)

        serialized_fooditems=foodserializer(cart.items.all(), many=True)
        return Response({
            'cart_data':serialized_cart.data,
            'food_item_data':serialized_fooditems.data
            },status=status.HTTP_200_OK)




class Search(APIView):
    

    def post(self,request):
        
        searchQuery=request.data['searchQuery']
        Searchedfooditems=FoodItem.objects.filter(item_name__icontains=searchQuery)
        Searchedfooditemsserialized=foodserializer(Searchedfooditems, many=True)
        return Response({
            'search_results':Searchedfooditemsserialized.data
        },status=status.HTTP_200_OK)


class DisplayFooditems(APIView):

    def get(self,request,item_name):

        fooditem = FoodItem.objects.filter(item_name=item_name).first()
        Res = Restaurent.objects.filter(Fooditems = fooditem)
        if Res.exists() :
            ResSerializedData = RestaurentSerializer(Res, many = True) 
        return Response({
            'Restaurents':ResSerializedData.data,
            },status=status.HTTP_200_OK)

 

class AdminLogin(APIView) :

    def post(self,request) :
        
        email = request.data['email']
        password = request.data['password']

        if not email and not password :
            return Response({
                'error':'password error'
            },status=status.HTTP_401_UNAUTHORIZED)
        
        
        user = authenticate(request, email = email, password = password)
        
        if user and user.isOwner == True :
            tokens = get_tokens_for_user(user)
            return Response({
                'access_token': tokens['access'],
                'refresh_token': tokens['refresh']
                
            }, status=status.HTTP_200_OK)
        
        
        if user and user.isOwner == False :
            return Response({
                'failure':'user authenticated but he is only the customer'
            })
        



class AdminSignUp(APIView) :

    def post(self, request) :

        AdminLoginSerializedData = Personserializer(data = request.data)

        if AdminLoginSerializedData.is_valid() :
            AdminLoginSerializedData.IsOwner = True
            AdminLoginSerializedData.save()

            return Response({
                'success' : 'True'
            }, status = status.HTTP_200_OK)
        
        
        else :
            return Response({
                'failure' : 'True'
            }, status = status.HTTP_400_BAD_REQUEST)



class Rest(APIView) :
    #permission_classes = [IsAuthenticated]
    def post(self, request) :

        user = request.user
        if user and user.isOwner == True :
            Rimg = request.data['img']
            Rname = request.data['Rname']
            Rdesc = request.data['Rdesc']
            address = request.data['address']
            RcontactNumber = request.data['RcontactNumber']


            if Restaurent.objects.filter(Radmin = user).exists():
                return Response({
                    'failure':'True'
                },status=status.HTTP_400_BAD_REQUEST)
            

            Robj = Restaurent.objects.create(Radmin = user, Rimg = Rimg, Rname =Rname, Rdesc = Rdesc, address = address, RcontactNumber = RcontactNumber)


            return Response({
                'success':'True'
            }, status = status.HTTP_200_OK)
        

    def get(self, request) :

        Restaurents = Restaurent.objects.all()
        SerializedData = RestaurentSerializer(Restaurents, many = True)

        return Response({
            'data':SerializedData.data
        },statu = status.HTTP_200_OK)
    
    

class AddtoRest(APIView) :
    permission_classes = [IsAuthenticated]

    
    def post(self, request, item_name) :

        user = request.user
        fooditem = FoodItem.objects.filter(item_name = item_name).first()
        Res = Restaurent.objects.filter(Radmin = user).first()

        if fooditem and Res :
            Res.Fooditems.add(fooditem)
            return Response({
                'success' : 'food item succesfully addded'
            }, status = status.HTTP_200_OK)
        
        else :
            return Response({
                'failure':'True'
            },status = status.HTTP_200_OK)
        
class DisplayUserOrder(APIView) :
    
    permission_classes = [IsAuthenticated]
    def get(self,request) :
        user = request.user
        OrderItems = order.objects.filter(User = user)
        if OrderItems.exists() :

            MainData = []

            for Orders in OrderItems:
                fooditem = Orders.fooditem.id
                fooditemData = FoodItem.objects.filter(id = fooditem).first()
                FoodItemSerializeData = foodserializer(fooditemData)
                additionalItem = AditionalFoodItems.objects.filter(order = Orders).first()
                OrderSerializedData = OrderSerializer(Orders)
                AddFoodItem = additionalItem.Additems.all()
                data = []
                for Add in AddFoodItem :
                    
                    #Add = FoodItem.objects.filter(id = Id).first()
                    AddFoodItemSerialized = foodserializer(Add)
                    data.append(AddFoodItemSerialized.data)
                
                MainData.append({
                    'OrderData':OrderSerializedData.data,
                    'FoodItem':FoodItemSerializeData.data,
                    'AdditionalItemsData':data
                })

            return Response({
                    'data':MainData
                })
            

        else :
            return Response({
                'failed':'order does not exist for this person'
            }, status = status.HTTP_404_NOT_FOUND)
        

class OrderOverview(APIView):
    def get(self, request, item_name) :
        fooditem = FoodItem.objects.filter(item_name = item_name).first()
        Res = Restaurent.objects.filter(Fooditems = fooditem ).first()

        Tfooditems = FoodItem.objects.all()

        count = 0

        for i in Tfooditems:
            count += 1

        Tdata = []

        for i in range(0,5) :
            index = random.randint(0,count-1)
            Tdata.append({
                'additems':foodserializer(Tfooditems[index]).data
            })
        
        return Response({
            'fooditem':foodserializer(fooditem).data,
            'Res':RestaurentSerializer(Res).data,
            'additems':Tdata
        }, status = status.HTTP_200_OK)
    
        





class OrderView(APIView) :


    permission_classes = [IsAuthenticated]

    def post(self, request) :
        user = request.user
        Rname = request.data['Rname']
        item_name = request.data['item_name']
        additional = request.data['additional']

        additionalFooditemslist = []
  
        if additional:       

            for ItemName in additional :
                addItem = FoodItem.objects.filter(item_name = ItemName).first()
                additionalFooditemslist.append(addItem)

        
        Res = Restaurent.objects.filter(Rname = Rname).first()
        fooditem = FoodItem.objects.filter(item_name = item_name).first()

        
    

        payementSum = int(fooditem.item_price)

        if additional:
            for items in additionalFooditemslist :
                payementSum += int(items.item_price)


        currency = 'usd'

        intent = stripe.PaymentIntent.create(
            amount = payementSum,
            currency = currency,
            payment_method_types = ['card'],
            metadata = {
                'email' : user.email,
                'Resid' : Res.id
            }
        )

        return Response({
            'client_secret' : intent['client_secret'],
            'Payment' : payementSum
        },status=status.HTTP_200_OK)





        








    


















































