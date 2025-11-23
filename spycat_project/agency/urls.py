from rest_framework.routers import DefaultRouter
from .views import CatViewSet, MissionViewSet

router = DefaultRouter()
router.register(r'cats', CatViewSet)
router.register(r'missions', MissionViewSet)

urlpatterns = router.urls