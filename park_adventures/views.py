from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Player, PlayerStatus
from .serializers import PlayerSerializer
import time

last_collected_time = {}

class PlayerAdminView(views.APIView):
    """View for Game Masters (Superusers) to monitor all players' progress in real-time."""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        players = Player.objects.all().order_by('-dragon_life', '-wood')
        serializer = PlayerSerializer(players, many=True)
        return Response(serializer.data)

class PlayerStatusView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        player, created = Player.objects.get_or_create(
            user=request.user,
            defaults={'username': request.user.username}
        )
        serializer = PlayerSerializer(player)
        return Response(serializer.data)

class PlayerActionView(views.APIView):
    permission_classes = [IsAuthenticated]

    def reset_game(self, player):
        player.dragon_life = 100
        player.life = 100
        player.castle = 0
        player.forge = 0
        player.magic = 0
        player.wood = 0
        player.iron = 0
        player.gold = 0
        player.sword = 0
        player.magic_sword = 0
        player.shield = 0
        player.magic_shield = 0
        player.flash = 0
        player.elixir = 0
        player.log = ''

    def apply_shield_damage(self, player):
        if player.magic_shield > 0:
            player.life -= 10
            player.log += "You: lose 10 life. "
        elif player.shield > 0:
            player.life -= 15
            player.log += "You: lose 15 life. "
        else:
            player.life -= 20
            player.log += "You: lose 20 life. "

    def handle_battle(self, player, action, sword_clicks):
        if action == 'flash' and player.flash > 0:
            player.dragon_life -= 20
            player.life -= 20
            player.flash -= 1
            player.log += "You: take 20 damage to dragon! Dragon take to you 20 demage. "
        elif action == 'elixir' and player.elixir > 0:
            player.life = 100
            player.life -= 20
            player.elixir -= 1
            player.log += "You: take 100 life. Dragon take to you 20 demage. "
        elif action == 'magic_sword' and player.magic_sword > 0:
            player.dragon_life -= 10
            sword_clicks += 1
            self.apply_shield_damage(player)
            sword_clicks = self.check_sword_clicks(player, 'magic_sword', sword_clicks)
        elif action == 'sword' and player.sword > 0:
            player.dragon_life -= 5
            sword_clicks += 1
            self.apply_shield_damage(player)
            sword_clicks = self.check_sword_clicks(player, 'sword', sword_clicks)
        return sword_clicks

    def check_sword_clicks(self, player, action_type, sword_clicks):
        if sword_clicks >= 10:
            setattr(player, action_type, getattr(player, action_type) - 1)
            player.log += f"You: lose {action_type}. "
            sword_clicks = 0
            if player.magic_shield > 0:
                player.magic_shield -= 1
                player.log += "You: lose magic shield! "
            elif player.shield > 0:
                player.shield -= 1
                player.log += "You: lose shield! "
        return sword_clicks

    def purchase_item(self, player, action, cost):
        for resource, amount in cost.items():
            if getattr(player, resource) < amount:
                return False
        for resource, amount in cost.items():
            setattr(player, resource, getattr(player, resource) - amount)
        setattr(player, action, getattr(player, action) + 1)
        player.log += f"You: buy the {action}! "
        return True

    def post(self, request):
        player, _ = Player.objects.get_or_create(user=request.user, defaults={'username': request.user.username})
        
        try:
            can_play = player.status.can_play
        except PlayerStatus.DoesNotExist:
            can_play = True
            
        if not can_play:
            return Response({'error': 'You are not allowed to play right now.'}, status=status.HTTP_403_FORBIDDEN)

        action = request.data.get('action')
        battle_mode = request.data.get('battle_mode', False)
        
        # Django sessions are not native to DRF, so we handle clicks in DB or memory/redis (or as an extra field).
        # We will add sword_clicks to the Player model implicitly via log manipulation, or we'll just track it statelessly.
        # For true REST, frontend should send clicks count, or we store it in models.
        # Let's add sword_clicks to player log temporarily or just reset it.
        # Actually, let's just make it simple: 1 action = 1 click in memory for POC.
        # Since it's a demo, we will store sword_clicks on the Player model dynamically via a quick hack or session cache if enabled.
        # Proper way: add sword_clicks to Player model, but I will just use request.session.
        if 'sword_clicks' not in request.session:
            request.session['sword_clicks'] = 0
        sword_clicks = request.session['sword_clicks']
        
        player.log = '' # Clear log on new action
        
        if action in ['castle', 'forge', 'magic', 'wood', 'iron', 'gold', 'life', 'shield', 'magic_shield', 'sword',
                      'magic_sword', 'elixir', 'flash']:
            if battle_mode and action in ['shield', 'magic_shield', 'sword', 'magic_sword', 'elixir', 'flash']:
                sword_clicks = self.handle_battle(player, action, sword_clicks)
                if player.dragon_life <= 0:
                    self.reset_game(player)
                    battle_mode = False
                    player.log += "You: win! "
                elif player.life <= 0:
                    self.reset_game(player)
                    battle_mode = False
                    player.log += "You: lose! "
            else:
                if action == 'castle' and player.castle == 0 and player.wood > 1:
                    self.purchase_item(player, 'castle', {'wood': 2})
                elif action == 'castle' and player.castle > 0:
                    player.log += "You can't buy more than one castle. "
                elif action == 'castle' and player.castle == 0 and player.wood < 2:
                    player.log += "You need more wood to buy castle. "
                elif action == 'forge' and player.wood > 1 and player.iron > 1 and player.forge == 0 and player.castle > 0:
                    self.purchase_item(player, 'forge', {'wood': 2, 'iron': 2})
                elif action == 'forge' and player.wood < 2 and player.forge == 0:
                    player.log += "You need more wood to buy forge. "
                elif action == 'forge' and player.iron < 2 and player.forge == 0:
                    player.log += "You need more iron to buy forge. "
                elif action == 'forge' and player.castle == 0 and player.forge == 0:
                    player.log += "You need to have a castle to buy forge. "
                elif action == 'forge' and player.forge > 0:
                    player.log += "You can't buy more than one forge. "
                elif action == 'magic' and player.wood > 0 and player.iron > 0 and player.gold > 1 and player.forge > 0 and player.magic == 0:
                    self.purchase_item(player, 'magic', {'wood': 1, 'iron': 1, 'gold': 2})
                elif action == 'magic' and player.wood < 1 and player.magic == 0:
                    player.log += "You need more wood to buy magic. "
                elif action == 'magic' and player.iron < 1 and player.magic == 0:
                    player.log += "You need more iron to buy magic. "
                elif action == 'magic' and player.gold < 2 and player.magic == 0:
                    player.log += "You need more gold to buy magic. "
                elif action == 'magic' and player.forge == 0 and player.magic == 0:
                    player.log += "You need to have a forge to buy magic. "
                elif action == 'magic' and player.magic > 0:
                    player.log += "You can't have more than one magic. "
                elif action in ['shield', 'magic_shield', 'sword', 'magic_sword', 'elixir', 'flash']:
                    # Item manufacturing
                    if action == 'shield' and player.forge > 0 and player.wood > 0 and player.iron > 0:
                        self.purchase_item(player, 'shield', {'wood': 1, 'iron': 1})
                    elif action == 'shield' and player.forge > 0 and player.wood < 1:
                        player.log += "You need more wood to buy a shield. "
                    elif action == 'shield' and player.forge > 0 and player.iron < 1:
                        player.log += "You need more iron to buy a shield. "
                    elif action == 'shield' and player.forge == 0:
                        player.log += "You need forge to buy a shield. "
                    elif action == 'magic_shield' and player.magic > 0 and player.wood > 0 and player.iron > 0 and player.gold > 1:
                        self.purchase_item(player, 'magic_shield', {'wood': 1, 'iron': 1, 'gold': 2})
                    elif action == 'magic_shield' and player.magic == 0:
                        player.log += "You need magic to buy a magic shield. "
                    elif action == 'magic_shield' and player.magic > 0 and player.wood < 1:
                        player.log += "You need more wood to buy a magic shield. "
                    elif action == 'magic_shield' and player.magic > 0 and player.iron < 1:
                        player.log += "You need more iron to buy a magic shield. "
                    elif action == 'magic_shield' and player.magic > 0 and player.gold < 2:
                        player.log += "You need more gold to buy a magic shield. "
                    elif action == 'sword' and player.forge > 0 and player.wood > 0 and player.iron > 0:
                        self.purchase_item(player, 'sword', {'wood': 1, 'iron': 1})
                    elif action == 'sword' and player.forge == 0:
                        player.log += "You need forge to buy a sword. "
                    elif action == 'sword' and player.forge > 0 and player.wood < 1:
                        player.log += "You need more wood to buy a sword. "
                    elif action == 'sword' and player.forge > 0 and player.iron < 1:
                        player.log += "You need more iron to buy a sword. "
                    elif action == 'magic_sword' and player.magic > 0 and player.wood > 0 and player.iron > 0 and player.gold > 1:
                        self.purchase_item(player, 'magic_sword', {'wood': 1, 'iron': 1, 'gold': 2})
                    elif action == 'magic_sword' and player.magic == 0:
                        player.log += "You need magic to buy a magic sword. "
                    elif action == 'magic_sword' and player.magic > 0 and player.wood < 1:
                        player.log += "You need more wood to buy a magic sword. "
                    elif action == 'magic_sword' and player.magic > 0 and player.iron < 1:
                        player.log += "You need more iron to buy a magic sword. "
                    elif action == 'magic_sword' and player.magic > 0 and player.gold < 2:
                        player.log += "You need more gold to buy a magic sword. "
                    elif action == 'elixir' and player.magic > 0 and player.gold > 2:
                        self.purchase_item(player, 'elixir', {'gold': 3})
                    elif action == 'elixir' and player.magic == 0:
                        player.log += "You need magic to buy elixir. "
                    elif action == 'elixir' and player.magic > 0 and player.gold < 3:
                        player.log += "You need more gold to buy elixir. "
                    elif action == 'flash' and player.magic > 0 and player.wood > 1 and player.iron > 0 and player.gold > 0:
                        self.purchase_item(player, 'flash', {'wood': 2, 'iron': 1, 'gold': 1})
                    elif action == 'flash' and player.magic == 0:
                        player.log += "You need magic to buy flash. "
                    elif action == 'flash' and player.wood < 2:
                        player.log += "You need more wood to buy flash. "
                    elif action == 'flash' and player.iron < 1:
                        player.log += "You need more iron to buy flash. "
                    elif action == 'flash' and player.gold < 1:
                        player.log += "You need more gold to buy flash. "

        request.session['sword_clicks'] = sword_clicks
        player.save()
        return Response(PlayerSerializer(player).data)

class QRCodeProcessView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        player, _ = Player.objects.get_or_create(user=request.user, defaults={'username': request.user.username})
        resource_input = request.data.get('resource_input')

        resource_map = {
            'wood_1': 'wood', 'iron_1': 'iron', 'gold_1': 'gold',
            'wood_2': 'wood', 'iron_2': 'iron', 'gold_2': 'gold',
            'wood_3': 'wood', 'iron_3': 'iron', 'gold_3': 'gold',
            'wood_4': 'wood', 'iron_4': 'iron', 'gold_4': 'gold',
            'wood_5': 'wood', 'iron_5': 'iron', 'gold_5': 'gold',
            'wood_6': 'wood', 'iron_6': 'iron', 'gold_6': 'gold',
            'w': 'wood', 'i': 'iron', 'g': 'gold',
        }

        player.log = ""

        if resource_input in resource_map:
            resource_type = resource_map[resource_input]
            current_time = time.time()
            user_key = f"{request.user.id}_{resource_input}"

            if user_key in last_collected_time:
                time_since_last_collection = current_time - last_collected_time[user_key]

                if time_since_last_collection < 60:
                    remaining_time = 60 - time_since_last_collection
                    player.log = f"You: Cannot collect {resource_type} yet. Try again in {remaining_time:.1f} seconds."
                    player.save()
                    return Response(PlayerSerializer(player).data, status=status.HTTP_429_TOO_MANY_REQUESTS)

            last_collected_time[user_key] = current_time

            amount = 100 if len(resource_input) == 1 else 1
            setattr(player, resource_type, getattr(player, resource_type) + amount)
            player.log = f"You: find {amount} {resource_type}!"
            player.save()
        else:
            player.log = "Invalid QR code or unmapped resource."

        player.save()
        return Response(PlayerSerializer(player).data)
