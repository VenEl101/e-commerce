from django.db.models import Model, DateTimeField


class TimeBaseModel(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)


    class Meta:
        abstract = True


