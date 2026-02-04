from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("mesa/<str:id_mesa>/", views.mesa_detail, name="mesa_detail"),
    path("mesa/<str:id_mesa>/reservar/", views.mesa_reservar, name="mesa_reservar"),
    path("mesa/<str:id_mesa>/marcar-pago/", views.mesa_marcar_pago, name="mesa_marcar_pago"),
    path("mesa/<str:id_mesa>/cancelar/", views.mesa_cancelar_reserva, name="mesa_cancelar_reserva"),
    path("mesa/<str:id_mesa>/desfazer-venda/", views.mesa_desfazer_venda, name="mesa_desfazer_venda"),
    path("relatorio/", views.relatorio, name="relatorio"),
    path("imagem-mapa/", views.imagem_mapa, name="imagem_mapa"),
]
