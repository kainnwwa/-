import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import GameState


class GameConsumer(AsyncWebsocketConsumer):
    # Храним список подключённых игроков
    connected_players = {}  # channel_name -> player_number
    next_player_num = 1

    async def connect(self):
        # Определяем номер игрока
        GameConsumer.next_player_num += 1
        self.num = GameConsumer.next_player_num - 1
        GameConsumer.connected_players[self.channel_name] = self.num

        await self.channel_layer.group_add("game", self.channel_name)
        await self.accept()

        self.g = await sync_to_async(lambda: GameState.objects.get_or_create(id=1)[0])()

        await self.send_json({
            "type": "init",
            "num": self.num,
            "turn": self.g.current_turn,
            "city": self.g.last_city,
            "is_over": self.g.is_over,
        })

    async def disconnect(self, code):
        await self.channel_layer.group_discard("game", self.channel_name)
        if self.channel_name in GameConsumer.connected_players:
            del GameConsumer.connected_players[self.channel_name]

    async def receive(self, text_data):
        d = json.loads(text_data)
        if d.get("action") == "surrender":
            await self.end_game()
        elif d.get("action") == "city":
            await self.play_city(d["city"].strip().capitalize())

    async def play_city(self, city):
        if not city:
            return await self.err("Введите город")
        if self.g.is_over:
            return await self.err("Игра завершена")
        if self.g.current_turn != self.num:
            return await self.err("Не ваш ход")
        if city in self.g.used_cities_list:
            return await self.err("Город уже был")

        if self.g.last_city:
            last = self.g.last_city[-1].lower()
            need = self.g.last_city[-2].lower() if last in "ьыъ" else last
            if city[0].lower() != need:
                return await self.err(f"Нужна буква {need.upper()}")

        await sync_to_async(self._save)(city)
        last = city[-1].lower()
        letter = city[-2].lower() if last in "ьыъ" else last
        nxt = 2 if self.num == 1 else 1
        await self.channel_layer.group_send("game", {
            "type": "city",
            "city": city,
            "letter": letter.upper(),
            "turn": nxt,
            "from": self.num
        })

    async def end_game(self):
        if self.g.is_over:
            return
        winner = 2 if self.num == 1 else 1
        await sync_to_async(lambda: setattr(GameState.objects.get(id=1), 'is_over', True) or
                            GameState.objects.get(id=1).save())()
        await self.channel_layer.group_send("game",
            {"type": "over", "msg": f"Игрок {self.num} сдался. Победил {winner}!"})

    def _save(self, city):
        g = GameState.objects.get(id=1)
        g.used_cities = f"{g.used_cities},{city}" if g.used_cities else city
        g.last_city = city
        g.current_turn = 2 if self.num == 1 else 1
        g.save()

    async def city(self, e):
        await self.send_json({"type": "city", **{k: e[k] for k in ("city", "letter", "turn", "from")}})

    async def over(self, e):
        await self.send_json({"type": "over", "msg": e["msg"]})

    async def err(self, msg):
        await self.send_json({"type": "error", "message": msg})

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))