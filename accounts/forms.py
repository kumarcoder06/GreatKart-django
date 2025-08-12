from django import forms
from .models import Account , UserProfile


from django import forms
from .models import Account

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password' ,'autocomplete': 'new-password'})
    )

    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name','autocomplete': 'off'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name','autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address','autocomplete': 'off'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number','autocomplete': 'off'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match!")  


    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists!")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')

        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")

        if len(phone_number) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")

        return phone_number
    
class UserForm(forms.ModelForm):
    class Meta:
        model = Account 
        fields = ('first_name','last_name','phone_number')

    def __init__(self,*args,**kwargs):
        super(UserForm,self).__init__(*args,**kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False,error_messages={'invalid':("image files only")},widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ('address_line_1','address_line_2','city','state','country','pincode','profile_picture')


    def __init__(self,*args,**kwargs):
        super(UserProfileForm,self).__init__(*args,**kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    