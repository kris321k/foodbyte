from django.contrib import admin
from django.urls import path
from .import views
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/',views.submitData.as_view()),
    path('login/',views.login.as_view()),
    path('profile/',views.profile.as_view()),
    path('home/',views.home.as_view()),
    path('home/<str:category_name>',views.home.as_view()),
    path('review/<str:item_name>/', views.review.as_view(), name='add_review'),
    path('review/<str:item_name>/<int:review_id>/',views.Reviewpatch.as_view()),
    path('ForgotPassword/',views.ForgotPassword.as_view()),
    #path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    #path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verifyOtp/',views.verifyOtp.as_view()),
    path('Cartaccess/<str:item_name>',views.Cartaccess.as_view()),
    path('displayCart/',views.displayCart.as_view()),
    path('Cartaccess/',views.Cartaccess.as_view()),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('category/<str:category_name>',views.displayCategories.as_view())



    

]

