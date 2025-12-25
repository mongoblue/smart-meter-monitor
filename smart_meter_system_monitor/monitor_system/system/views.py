from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import SystemOption
from .serializers import OptionSerializer


class OptionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        opts = SystemOption.objects.all()
        ser = OptionSerializer(opts, many=True)
        return Response(ser.data)


class OptionUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):        # ← 改成 post
        opt = get_object_or_404(SystemOption, pk=pk, editable=True)
        opt.value = request.data.get('value', opt.value)
        opt.save()
        return Response(OptionSerializer(opt).data)