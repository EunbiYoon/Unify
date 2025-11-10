# finance/urls.py
from django.urls import path
from ninja import NinjaAPI
from .views import (
    pred_router, sap_router, cctr_router, rakey_router,
    gate_router, process_router, merge_router,
    close_router, db_router, home_router
)

api = NinjaAPI(version="2.0.0")
api.add_router("/home", home_router)
api.add_router("/prediction", pred_router)
api.add_router("/sap", sap_router)
api.add_router("/cctr", cctr_router)
api.add_router("/gate", gate_router)
api.add_router("/rakey", rakey_router)
api.add_router("/process", process_router)
api.add_router("/merge", merge_router)
api.add_router("/close", close_router)
api.add_router("/db", db_router)

urlpatterns = [
    path("", api.urls),
]