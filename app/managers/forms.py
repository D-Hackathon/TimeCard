from django import forms

class EmployeeIDSearchForm(forms.Form):
    employee_id = forms.CharField(
        label="社員ID",
        required=True,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "社員IDを入力してください"})
    )