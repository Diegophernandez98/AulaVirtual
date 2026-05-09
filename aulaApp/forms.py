from django import forms
from aulaApp.models import TipoUsuario, Disponibilidad, DisponibilidadMultiple
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError


DIAS_CHOICES = [
    (1, 'Lunes'),
    (2, 'Martes'),
    (3, 'Miércoles'),
    (4, 'Jueves'),
    (5, 'Viernes'),
    (6, 'Sábado'),
    (7, 'Domingo'),
]

# --- DEFINICIÓN DE BloqueIndividualForm (AÑADIR ESTO) ---
class BloqueIndividualForm(forms.ModelForm):
    class Meta:
        model = Disponibilidad
        fields = ['fecha', 'hora_inicio', 'hora_fin']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'fecha': 'Selecciona la Fecha',
            'hora_inicio': 'Hora de Inicio',
            'hora_fin': 'Hora de Término',
        }
    
    # Opcional: Validación para asegurar que hora_fin sea posterior a hora_inicio
    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise ValidationError("La hora de término debe ser posterior a la hora de inicio.")
        return cleaned_data
# -----------------------------------------------------------


# --- DEFINICIÓN DE BloqueMultipleForm (Verificar que esté así) ---
class BloqueMultipleForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadMultiple
        fields = ['fecha_inicio', 'fecha_fin', 'dia_semana', 'hora_inicio', 'hora_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'dia_semana': forms.Select(choices=DIAS_CHOICES, attrs={'class': 'form-select'}), # Usamos Select para elegir el día
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        labels = {
            'fecha_inicio': 'Fecha de Inicio (Semana)',
            'fecha_fin': 'Fecha de Término (Semana)',
            'dia_semana': 'Día de la Semana',
            'hora_inicio': 'Hora de Inicio (Bloque)',
            'hora_fin': 'Hora de Término (Bloque)',
        }

    # Opcional: Validación para asegurar que hora_fin sea posterior a hora_inicio
    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")

        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise ValidationError("La hora de término debe ser posterior a la hora de inicio.")
        return cleaned_data
    
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
    class Meta:
        model = Disponibilidad
        fields = ['fecha', 'hora_inicio', 'hora_fin']  # <--- 'fecha' DEBE estar aquí
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
        
class AgendarClaseForm(forms.Form):
    pass