import random
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import GameRoom, Player, GameAction, ChatMessage
from .serializers import GameRoomSerializer, PlayerSerializer, GameActionSerializer, ChatMessageSerializer


class GameRoomViewSet(viewsets.ModelViewSet):
    queryset = GameRoom.objects.all().order_by('-created_at')
    serializer_class = GameRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        room = self.get_object()
        if room.status != 'lobby':
            return Response({'error': 'Кімната вже почала гру або завершена'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already joined
        if Player.objects.filter(room=room, user=request.user).exists():
            return Response({'status': 'Вже приєднані', 'room': GameRoomSerializer(room).data})

        Player.objects.create(room=room, user=request.user)
        # In a real app with WebSockets, broadcast an update event here
        return Response({'status': 'Успішно приєднались', 'room': GameRoomSerializer(room).data})

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        room = self.get_object()
        if room.host != request.user:
            return Response({'error': 'Тільки хост може почати гру'}, status=status.HTTP_403_FORBIDDEN)
        if room.status != 'lobby':
            return Response({'error': 'Гра вже почалась'}, status=status.HTTP_400_BAD_REQUEST)

        players = list(room.players.all())
        if len(players) < 3: # usually 6+, but 3 for testing
            return Response({'error': 'Недостатньо гравців (мінімум 3)'}, status=status.HTTP_400_BAD_REQUEST)

        # Distribute roles
        total = len(players)
        mafia_count = max(1, total // 4)
        has_doctor = total >= 4
        has_detective = total >= 5

        roles = ['mafia'] * mafia_count
        if has_doctor: roles.append('doctor')
        if has_detective: roles.append('detective')
        
        while len(roles) < total:
            roles.append('townie')

        random.shuffle(roles)
        for i, player in enumerate(players):
            player.role = roles[i]
            player.save()

        room.status = 'night'
        room.phase_number = 1
        room.save()
        
        ChatMessage.objects.create(
            room=room,
            msg_type='system',
            text=f"Гра почалась! Настала Ніч {room.phase_number}. Місто засинає..."
        )

        return Response(GameRoomSerializer(room).data)

    @action(detail=True, methods=['post'])
    def submit_action(self, request, pk=None):
        """Player submits action (vote_kill, vote_lynch, heal, inspect)"""
        room = self.get_object()
        player = get_object_or_404(Player, room=room, user=request.user)
        
        if not player.is_alive:
            return Response({'error': 'Мертві не можуть діяти'}, status=status.HTTP_400_BAD_REQUEST)
        if room.status not in ['day', 'night']:
            return Response({'error': 'Гра не активна'}, status=status.HTTP_400_BAD_REQUEST)

        action_type = request.data.get('action_type')
        target_id = request.data.get('target_id')
        target = get_object_or_404(Player, id=target_id, room=room) if target_id else None

        # Validate by phase and role
        if room.status == 'night':
            if player.role == 'mafia' and action_type == 'vote_kill':
                pass # valid
            elif player.role == 'doctor' and action_type == 'heal':
                pass # valid (could add check to not heal self twice)
            elif player.role == 'detective' and action_type == 'inspect':
                if not target: return Response({"error": "No target"}, status=400)
                is_mafia = target.role == 'mafia'
                # Record silently
                GameAction.objects.update_or_create(
                    room=room, actor=player, phase_number=room.phase_number, is_night_action=True,
                    defaults={'target': target, 'action_type': action_type}
                )
                return Response({'status': 'ok', 'result': 'Мафія' if is_mafia else 'Містянин'})
            else:
                return Response({'error': 'Невірна дія для вашої ролі вночі'}, status=status.HTTP_400_BAD_REQUEST)
                
            # Upsert action to allow changing mind before night ends
            GameAction.objects.update_or_create(
                room=room, actor=player, phase_number=room.phase_number, is_night_action=True,
                defaults={'target': target, 'action_type': action_type}
            )
        else: # Day
            if action_type != 'vote_lynch':
                return Response({'error': 'Вдень можна тільки голосувати'}, status=status.HTTP_400_BAD_REQUEST)
            # Upsert
            GameAction.objects.update_or_create(
                room=room, actor=player, phase_number=room.phase_number, is_night_action=False,
                defaults={'target': target, 'action_type': action_type}
            )
            
        return Response({'status': 'Дію збережено'})

    @action(detail=True, methods=['post'])
    def next_phase(self, request, pk=None):
        """Host or system triggers the next phase, resolving actions."""
        room = self.get_object()
        if room.status == 'finished':
            return Response({'error': 'Гра вже завершена'}, status=400)
            
        alive_players = room.players.filter(is_alive=True)
        alive_mafia = alive_players.filter(role='mafia').count()
        alive_town = alive_players.exclude(role='mafia').count()

        if room.status == 'night':
            # Resolve Night actions
            actions = GameAction.objects.filter(room=room, phase_number=room.phase_number, is_night_action=True)
            
            # Mafia kill logic (majority vote or just pick the first targeted one if tied)
            kill_votes = actions.filter(action_type='vote_kill', target__is_alive=True)
            kill_target = None
            if kill_votes.exists():
                # Count votes
                targets = kill_votes.values('target').annotate(count=Count('target')).order_by('-count')
                kill_target_id = targets[0]['target']
                kill_target = Player.objects.get(id=kill_target_id)
            
            # Doctor heal logic
            heal_action = actions.filter(action_type='heal', target__is_alive=True).first()
            healed_target = heal_action.target if heal_action else None

            msg = f"Місто прокидається. Настав День {room.phase_number}. "
            if kill_target:
                if kill_target == healed_target:
                    msg += "Вночі мафія намагалася вбити жителя, але лікар його врятував!"
                else:
                    kill_target.is_alive = False
                    kill_target.save()
                    msg += f"Цієї ночі було вбито гравця {kill_target.user.username}. Його роль: {kill_target.get_role_display()}."
            else:
                msg += "Цієї ночі ніхто не постраждав."

            ChatMessage.objects.create(room=room, msg_type='system', text=msg)
            
            # Check Win
            if room.players.filter(is_alive=True, role='mafia').count() == 0:
                room.status = 'finished'
                ChatMessage.objects.create(room=room, msg_type='system', text="🎉 МІСТЯНИ ПЕРЕМОГЛИ! Усіх мафіозі знищено.")
            elif room.players.filter(is_alive=True, role='mafia').count() >= room.players.filter(is_alive=True).exclude(role='mafia').count():
                room.status = 'finished'
                ChatMessage.objects.create(room=room, msg_type='system', text="💀 МАФІЯ ПЕРЕМОГЛА! Місто захоплено.")
            else:
                room.status = 'day'
            room.save()

        elif room.status == 'day':
            # Resolve Day actions (Voting)
            actions = GameAction.objects.filter(room=room, phase_number=room.phase_number, is_night_action=False)
            vote_lynch = actions.filter(action_type='vote_lynch', target__is_alive=True)
            
            if vote_lynch.exists():
                targets = vote_lynch.values('target').annotate(count=Count('target')).order_by('-count')
                lynch_target_id = targets[0]['target']
                # Simplification: highest vote gets lynched. In real mafia, might require >50% or explicit skip
                lynch_target = Player.objects.get(id=lynch_target_id)
                lynch_target.is_alive = False
                lynch_target.save()
                
                msg = f"За результатами голосування, місто вирішило стратити {lynch_target.user.username}. Його роль: {lynch_target.get_role_display()}."
                ChatMessage.objects.create(room=room, msg_type='system', text=msg)

            room.phase_number += 1
            room.status = 'night'
            room.save()
            ChatMessage.objects.create(room=room, msg_type='system', text=f"Настала Ніч {room.phase_number}. Місто засинає...")
            
            # Check Win again after lynch
            if room.players.filter(is_alive=True, role='mafia').count() == 0:
                room.status = 'finished'
                ChatMessage.objects.create(room=room, msg_type='system', text="🎉 МІСТЯНИ ПЕРЕМОГЛИ! Усіх мафіозі знищено.")
                room.save()
            elif room.players.filter(is_alive=True, role='mafia').count() >= room.players.filter(is_alive=True).exclude(role='mafia').count():
                room.status = 'finished'
                ChatMessage.objects.create(room=room, msg_type='system', text="💀 МАФІЯ ПЕРЕМОГЛА! Місто захоплено.")
                room.save()

        return Response(GameRoomSerializer(room).data)


class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.request.query_params.get('room')
        if room_id:
            return Player.objects.filter(room_id=room_id)
        return super().get_queryset()


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ChatMessage.objects.all()
        room_id = self.request.query_params.get('room')
        if room_id:
            qs = qs.filter(room_id=room_id)
            
            # Filter mafia msgs if user is not mafia
            try:
                player = Player.objects.get(room_id=room_id, user=self.request.user)
                if player.role != 'mafia':
                    qs = qs.exclude(msg_type='mafia')
            except Player.DoesNotExist:
                qs = qs.exclude(msg_type='mafia')
            
            return qs
        return ChatMessage.objects.none()

    def perform_create(self, serializer):
        room_id = self.request.data.get('room')
        room = get_object_or_404(GameRoom, id=room_id)
        try:
            sender = Player.objects.get(room=room, user=self.request.user)
        except Player.DoesNotExist:
            sender = None # e.g. spectator, shouldn't really happen
            
        msg_type = self.request.data.get('msg_type', 'public')
        if msg_type == 'mafia' and sender and sender.role != 'mafia':
            msg_type = 'public' # Force public if not mafia trying to send mafia msg
            
        serializer.save(room=room, sender=sender, msg_type=msg_type)
