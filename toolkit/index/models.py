from __future__ import unicode_literals
from django.db import models
from django.core.exceptions import ValidationError


class IndexLink(models.Model):

    text = models.CharField(max_length=1024, blank=True, null=False)
    link = models.URLField(max_length=1024, blank=False, null=False)
    category = models.ForeignKey(
        "IndexCategory",
        verbose_name="Link category",
        related_name="links",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "IndexLinks"
        ordering = [
            "category",
        ]

    def clean(self):
        if self.link:
            self.link = self.link.strip()
        if self.text:
            self.text = self.text.strip()

    def __str__(self):
        return self.text if self.text else self.link


class IndexCategory(models.Model):

    name = models.CharField(max_length=1024, blank=False, null=False)

    class Meta:
        db_table = "IndexLinkCategories"

    def clean(self):
        if self.name:
            self.name = self.name.strip()
            if len(self.name) == 0:
                raise ValidationError("Name cannot be blank")

    def __str__(self):
        return self.name
