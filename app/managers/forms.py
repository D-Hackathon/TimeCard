from django import forms

class EmployeeIDSearchForm(forms.Form):
    # 社員ID入力にCSSクラスを付与してテンプレートのスタイルを適用する
    employee_id = forms.CharField(
        label="社員ID",
        required=True,
        widget=forms.TextInput(attrs={"class": "input"})
    )