from django import forms

class EmployeeIDSearchForm(forms.Form):
    employee_id = forms.IntegerField(label="社員ID",required=True)