from django.db import models

class GameState(models.Model):
    last_city = models.CharField(max_length=100, default="")
    used_cities = models.TextField(default="")
    current_turn = models.IntegerField(default=1)
    is_over = models.BooleanField(default=False)

    @property
    def used_cities_list(self):
        return self.used_cities.split(",") if self.used_cities else []