from django import forms
from aulaApp.models import TipoUsuario, Disponibilidad
from django.utils import timezone
import datetime

class LoginUsuario(forms.Form):
    username = forms.CharField(max_length=50, required=True, label="Nombre de usuario")
    password = forms.CharField(max_length=50, required=True, label="Contraseña")


class RegistroUsuarioForm(forms.Form):
    username = forms.CharField(max_length=50, required=True, label="Nombre de usuario")
    nombre = forms.CharField(max_length=50, required=True, label="Nombre")
    apellido = forms.CharField(max_length=50, required=True, label="Apellido")
    email = forms.EmailField(max_length=254, required=True, label="Correo Electrónico")

    tipo_usuario = forms.ModelChoiceField(
        queryset=TipoUsuario.objects.all(), #Lee las opciones desde la BD
        label="Tipo de Usuario",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    password = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.PasswordInput,
        label="Contraseña")
    confirm_password = forms.CharField(
        max_length=100, 
        required=True, 
        widget=forms.PasswordInput, 
        label="Ingrese nuevamente su contraseña para confirmar")


    #validar email - protección ante ataques básicos (XSS)
    def clean_email(self):
        from .models import Usuario 
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email


    #validar username
    def clean_username(self):
        from .models import Usuario
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username
    

    #validar si las contraseñas son iguales
    def clean(self):
        #llamar método clean()
        cleaned_data = super().clean() 
        
        pass1 = cleaned_data.get("password")
        pass2 = cleaned_data.get("confirm_password")

        if pass1 and pass2 and pass1 != pass2:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        
        return cleaned_data
    



class DisponibilidadForm(forms.ModelForm):
    # Definimos los meses en español
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    # Campos "falsos" que no se guardan directo en la BD, sirven para construir la fecha
    dia = forms.IntegerField(
        min_value=1, 
        max_value=31, 
        label="Día",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 15'})
    )
    mes = forms.ChoiceField(
        choices=MESES, 
        label="Mes",
        widget=forms.Select(attrs={'class': 'form-select'}) # 'form-select' es estilo Bootstrap
    )

    class Meta:
        model = Disponibilidad
        # EXCLUIMOS 'fecha' porque la calcularemos nosotros
        fields = ['hora_inicio', 'hora_fin'] 
        widgets = {
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}), 
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }



# En forms.py

    def clean(self):
        cleaned_data = super().clean()
        dia = cleaned_data.get("dia")
        mes = cleaned_data.get("mes")
        
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")

        # --- CORRECCIÓN AQUÍ ---
        # Antes bloqueábamos si hora_fin <= hora_inicio.
        # Ahora permitimos hora_fin < hora_inicio (asumiendo que es al día siguiente).
        # Solo bloqueamos si son EXACTAMENTE iguales (clase de 0 minutos).
        if hora_inicio and hora_fin and hora_inicio == hora_fin:
            self.add_error('hora_fin', "La hora de inicio y término no pueden ser iguales.")
        # -----------------------

        if dia and mes:
            try:
                ahora_chile = timezone.localtime(timezone.now())
                hoy = ahora_chile.date()
                hora_actual = ahora_chile.time()
                
                year_actual = hoy.year
                mes_int = int(mes)
                
                # 1. Construimos la fecha tentativa
                fecha_construida = datetime.date(year=year_actual, month=mes_int, day=dia)
                
                # 2. Lógica de Año Inteligente
                if mes_int < hoy.month:
                    fecha_construida = datetime.date(year=year_actual + 1, month=mes_int, day=dia)
                
                # 3. VALIDACIÓN DE FECHA Y HORA
                
                # A) Si la fecha de INICIO es pasado
                if fecha_construida < hoy:
                    self.add_error('dia', "No puedes crear una hora en una fecha pasada.")
                
                # B) Si es HOY, validamos que la HORA DE INICIO no haya pasado
                elif fecha_construida == hoy and hora_inicio:
                    if hora_inicio < hora_actual:
                        self.add_error('hora_inicio', "Esa hora de inicio ya pasó.")

                cleaned_data['fecha_calculada'] = fecha_construida

            except ValueError:
                self.add_error('dia', "La fecha ingresada no es válida.")
        
        return cleaned_data

class AgendarClaseForm(forms.Form):
    pass