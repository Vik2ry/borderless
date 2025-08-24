from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from services.fx import FXService, FXServiceError

class DemoFXView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        src = request.query_params.get('from','USDx')
        dst = request.query_params.get('to','cNGN')
        fx = FXService()
        try:
            rate = fx.get_rate(src,dst)
        except FXServiceError as e:
            return Response({'error': str(e)}, status=400)
        return Response({'from': src, 'to': dst, 'rate': rate})

class DemoAuthPing(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'ok': True, 'user': request.user.username})
