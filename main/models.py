import json
import urllib.parse
from collections import Counter
from urllib.error import HTTPError

import challonge
from ckeditor_uploader.fields import RichTextUploadingField
from django import forms
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.timezone import now
from sorl.thumbnail import ImageField

from main.storage import OverwriteStorage

grades = {
    'xa': {
        14: [],
        15: [],
        16: ['a', 'b', 'c', 'd', 'e', 'f', 'j', 'p', 'r'],
        17: ['a', 'b', 'c', 'd', 'e', 'j', 'p', 'q', 'r'],
        18: ['r', 'q', 'j', 'p', 'd', 'e', 'b', 'a']
    },
    'htxcg': {
        19: []
    },
    'stxcg': {
        19: []
    },

    'xv': {
        17: [],
        18: []
    },
    'htxvg': {
        19: []
    },

    'xs': {
        17: [],
        18: [],
        19: []
    },

    'Tilst': {
        17: [],
        18: []
    },

    'stxtg': {
        19: []
    }
}

GRADES = ()
for school, years in grades.items():
    for year, classes in years.items():
        for class_ in classes:
            GRADES += (('{}{}{}'.format(year, school, class_),) * 2,)
        if not classes:
            GRADES += (('{}{}'.format(year, school),) * 2,)

GRADES_TEACHER = (('teacher', 'Lærer'),)  # Has to be last one

PAYTYPES = (
    ('mp', 'MobilePay'),
    ('cash', 'Kontant')
)


def profile_picture_path(instance, orig):
    ext = orig.split('.')[-1]
    filename = 'profile/{}-{}.{}'.format(instance.pk, int(now().timestamp()), ext)
    return filename


class Profile(models.Model):
    class Meta:
        verbose_name = 'profil'
        verbose_name_plural = 'profiler'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = ImageField(upload_to=profile_picture_path, storage=OverwriteStorage(), blank=True,
                       verbose_name='billede')
    bio = models.TextField(blank=True)
    grade = models.CharField(verbose_name='klasse', max_length=32, default='none')
    phone = models.CharField(validators=[RegexValidator(r'^\d{8}$')], max_length=16, null=True, blank=True,
                             verbose_name='telefonnummer', help_text='I dansk format f.eks. "12345678"')

    def __str__(self):
        return '{} ({})'.format(self.user.username, self.user.first_name)

    def get_grade_display(self):
        for k, v in GRADES_TEACHER:
            if k == self.grade:
                return v
        else:
            return self.grade


class StrippedMultipleChoiceFieldField(forms.MultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.pop('max_length')
        kwargs.pop('base_field')
        super().__init__(*args, **kwargs)


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.

    Uses Django 1.9's postgres ArrayField
    and a MultipleChoiceField for its formfield.

    Usage:

        choices = ChoiceArrayField(models.CharField(max_length=...,
                                                    choices=(...,)),
                                   default=[...])
    """

    def formfield(self, **kwargs):
        defaults = {
            'form_class': StrippedMultipleChoiceFieldField,
            'base_field': self.base_field.formfield(),
            'choices': self.base_field.choices,
        }
        defaults.update(kwargs)
        # Skip our parent's formfield implementation completely as we don't
        # care for it.
        # pylint:disable=bad-super-call
        return super().formfield(**defaults)


class Lan(models.Model):
    class Meta:
        verbose_name = 'LAN'
        verbose_name_plural = 'LAN'

    start = models.DateTimeField(verbose_name='start')
    end = models.DateTimeField(verbose_name='slut')
    open = models.DateTimeField(verbose_name='tildmelding åbner')
    name = models.CharField(max_length=255, verbose_name='navn')
    profiles = models.ManyToManyField(Profile, through='LanProfile')
    seats = models.TextField(verbose_name='pladser')
    blurb = RichTextUploadingField(verbose_name='blurb',
                                   help_text='Teksten, specifikt til dette lan, der bliver vist på forsiden.<br>'
                                             'Husk at wrappe tekst i &lt;p> tags!')
    paytypes = ChoiceArrayField(models.CharField(max_length=127, choices=PAYTYPES), verbose_name='betalingstyper',
                                null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='pris', null=True, blank=True)
    payphone = models.CharField(max_length=128, verbose_name='Betalingstelefonnummer', null=True, blank=True,
                                help_text='Skriv kun tal. (+45) skrives automatisk foran.')
    payment_manager_id = models.CharField(max_length=255, verbose_name="Payment Manager id", null=True, blank=True,
                                          help_text='Unik token som indentificerer hvor'
                                                    'betalingsforespørgelser skal sendes.')
    show_calendar = models.BooleanField(default=False, verbose_name='Vis kalender',
                                        help_text='Hvorvidt en kalender skal vises på forsiden. '
                                                  'Slå kun dette til hvis turneringer og andre events '
                                                  'efterhånden er ved at være klar.')
    food_open = models.BooleanField(default=False, verbose_name='Er madbestilling åben?')
    food_phone = models.CharField(max_length=128, verbose_name='madbestillingstelefonnummer', null=True, blank=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.start.strftime('%d. %b. %Y'))

    def is_open(self):
        return self.open <= now()

    is_open.short_description = 'Tilmelding åben?'

    def _parse_seats(self, lps):
        parsed = []
        tables = Counter()
        for row in self.seats.splitlines():
            if row[0] == '#':
                parsed.append(row[1:].strip())
                continue
            parsed.append([])
            for s in row:
                if s != '-':
                    tables[s] += 1
                    seat = '{}{:02d}'.format(s, tables[s])
                    try:
                        parsed[-1].append((seat, lps[seat]))
                    except KeyError:
                        parsed[-1].append((seat, None))
                else:
                    parsed[-1].append((None, None))
        return parsed, tables

    def parse_seats(self):
        lps = LanProfile.objects.filter(lan=self).select_related('profile', 'profile__user').all()
        lps_with_seat = lps.filter(seat__isnull=False)
        parsed, tables = self._parse_seats({lp.seat: lp for lp in lps_with_seat})
        return parsed, (len(lps), len(lps_with_seat), sum(tables.values()), len(lps.filter(seat__isnull=True)))

    def seats_count(self):
        lps = LanProfile.objects.filter(lan=self)
        parsed, tables = self._parse_seats({})
        return len(lps), len(lps.filter(seat__isnull=False)), sum(tables.values()), len(lps.filter(seat__isnull=True))

    @classmethod
    def get_next(cls, request=None):
        if request and hasattr(request, 'cached_lan'):
            return request.cached_lan
        try:
            lan = cls.objects.filter(end__isnull=False, end__gte=now()).latest('end')
        except cls.DoesNotExist:
            lan = None
        if request:
            request.cached_lan = lan
        return lan


class LanProfile(models.Model):
    class Meta:
        verbose_name = 'tilmelding'
        verbose_name_plural = 'tilmeldinger'
        unique_together = (('lan', 'seat'), ('lan', 'profile'))

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name='profil')
    lan = models.ForeignKey(Lan, on_delete=models.CASCADE, verbose_name='lan')
    seat = models.CharField(max_length=8, blank=True, null=True, verbose_name='plads')
    paytype = models.CharField(max_length=255, null=True, blank=True, verbose_name='betalingstype', choices=PAYTYPES)
    paid = models.NullBooleanField(verbose_name='betalt?')

    def __str__(self):
        return self.profile.user.username + '@' + self.lan.name

    def save(self, *args, **kwargs):
        if not self.seat:
            self.seat = None
        super().save(*args, **kwargs)

    def get_payment_url(self):
        attrs = {
            'amount': self.lan.price,
            'phone': self.lan.payphone,
            'comment': 'LAN|{}'.format(self.pk),
            'lock': '1'
        }
        return 'mobilepay://send?' + urllib.parse.urlencode(attrs)

    def get_payment_qr_url(self):
        attrs = {
            'chs': '300x300',
            'chld': 'M|2',
            'chl': self.get_payment_url(),
            'cht': 'qr'
        }

        return 'https://chart.googleapis.com/chart?' + urllib.parse.urlencode(attrs)


class Game(models.Model):
    class Meta:
        verbose_name = 'spil'
        verbose_name_plural = 'spil'

    name = models.CharField(max_length=255, verbose_name='navn')
    description = RichTextUploadingField(verbose_name='beskrivelse')
    image = ImageField(upload_to='games/', storage=OverwriteStorage(), blank=True,
                       verbose_name='billede')

    def __str__(self):
        return self.name


class Tournament(models.Model):
    class Meta:
        verbose_name = 'turnering'
        verbose_name_plural = 'turneringer'

    game = models.ForeignKey(Game, on_delete=models.CASCADE, verbose_name='spil')
    lan = models.ForeignKey(Lan, on_delete=models.CASCADE, verbose_name='lan')
    name = models.CharField(max_length=255, verbose_name='navn')
    description = RichTextUploadingField(verbose_name='beskrivelse')
    team_size = models.IntegerField(verbose_name='Holdstørrelse')
    challonge_id = models.IntegerField(verbose_name='Challonge id', help_text="Udfyles selv, når du trykker gem.",
                                       null=True, blank=True)
    extra_challonge = models.TextField(null=True, verbose_name='Extra challonge data', blank=True,
                                       help_text='Advannceret: ekstra data til challonge API. Angives i JSON format.')
    live = models.BooleanField(help_text='Er turneringen i gang? (viser live opdates på siden hvis ja)')
    open = models.BooleanField(verbose_name='Tilmelding mulig?',
                               help_text='Er der åbent for tilmelding? Hvis nej bliver turneringen ikke vist på siden.'
                                         'Bemærk at LanCrew medlemmer dog altid kan tilmelde sig.')
    start = models.DateTimeField(verbose_name='Start', null=True)
    end = models.DateTimeField(verbose_name='Slut', null=True, blank=True)
    allow_external = models.BooleanField(verbose_name='Tillad ikke LAN brugere',
                                         help_text='Hvis ja, kan der tilføjes personer'
                                                   'som ikke er tilmeldt LAN til ens hold.')
    owner = models.ForeignKey(Profile, on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name='Ansvarlig')
    show_on_calendar = models.BooleanField(verbose_name='Vis på kalender', default=True)

    def __str__(self):
        return self.name

    def get_challonge_url(self):
        return '{}_{}_{}'.format('aarhusgymnasiumlan', self.lan.id, self.id)

    def get_absolute_url(self):
        return reverse('tournament', kwargs={'game': self.game.name, 'lan_id': self.lan.id, 'name': self.name})


@receiver(post_save, sender=Tournament, dispatch_uid='create_challonge')
def create_challonge(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    if created:
        params = {
            'description': instance.description
        }
        if instance.extra_challonge:
            params.update(json.loads(instance.extra_challonge))
        try:
            tournament = challonge.tournaments.create(
                '{} – {} – {}'.format('AG LAN', instance.lan.name, instance.name),
                instance.get_challonge_url(),
                params.get('tournament_type', 'single elimination'), **params)
            instance.challonge_id = tournament['id']
            instance.save()
        except HTTPError:
            pass
    elif instance.challonge_id:
        url_params = {
            'game': instance.game.name,
            'lan_id': instance.lan.id,
            'name': instance.name
        }
        params = {
            'description': '{}<br><br>Tilmeld dig på: '
                           '<a href="https://aglan.dk{}" '
                           'target="_blank">{}</a>'.format(instance.description,
                                                           reverse('tournament', kwargs=url_params),
                                                           'AGLAN.dk'),
            'name': '{} – {} – {}'.format('AG LAN', instance.lan.name, instance.name),
            'url': instance.get_challonge_url()
        }
        if instance.extra_challonge:
            params.update(json.loads(instance.extra_challonge))
        try:
            challonge.tournaments.update(instance.challonge_id, **params)
        except HTTPError:
            pass


@receiver(pre_delete, sender=Tournament, dispatch_uid='delete_challonge')
def delete_challonge(sender, instance, **kwargs):
    try:
        challonge.tournaments.destroy(instance.challonge_id)
    except HTTPError:
        pass


class NamedProfile(models.Model):
    class Meta:
        verbose_name = 'anonym profil'
        verbose_name_plural = 'anonyme profiler'

    name = models.CharField(max_length=255, verbose_name='navn')

    def __str__(self):
        return self.name


class TournamentTeam(models.Model):
    class Meta:
        verbose_name = 'hold'
        verbose_name_plural = 'hold'
        unique_together = (('name', 'tournament'),)

    profiles = models.ManyToManyField(Profile, verbose_name='medlemmer')
    namedprofiles = models.ManyToManyField(NamedProfile, verbose_name='andre medlemmer')
    name = models.CharField(max_length=255, verbose_name='holdnavn')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True)
    challonge_id = models.IntegerField(verbose_name='Challonge id', help_text='Udfyldes selv, når du trykker gem.',
                                       null=True, blank=True)

    def __str__(self):
        return self.name

    def get_all(self):
        return list(self.profiles.all()) + list(self.namedprofiles.all())


@receiver(post_save, sender=TournamentTeam, dispatch_uid='create_challonge_team')
def create_challonge_team(sender, instance, **kwargs):
    created = kwargs.get('created', False)
    if created:
        try:
            participant = challonge.participants.create(instance.tournament.challonge_id,
                                                        instance.name,
                                                        misc=instance.id)
            instance.challonge_id = participant['id']
            instance.save()
        except HTTPError:
            pass


@receiver(pre_delete, sender=TournamentTeam, dispatch_uid='delete_challonge_team')
def delete_challonge_team(sender, instance, **kwargs):
    try:
        challonge.participants.destroy(instance.tournament.challonge_id, instance.challonge_id)
    except HTTPError:
        pass


class Event(models.Model):
    class Meta:
        verbose_name = 'begivenhed'
        verbose_name_plural = 'begivenheder'

    lan = models.ForeignKey(Lan, on_delete=models.CASCADE, verbose_name='lan')
    name = models.CharField(max_length=255, verbose_name='navn')
    url = models.URLField(max_length=255, verbose_name='link',
                          help_text='Valgfri. Link som kan klikkes på kalenderen.'
                                    'Denne felt har større prioritet end tekst.',
                          null=True, blank=True)
    text = RichTextUploadingField(verbose_name='tekst til eventside',
                                  help_text='Advarsel: Dette felt overskrives af url!',
                                  null=True, blank=True)
    start = models.DateTimeField(verbose_name='Start', null=True)
    end = models.DateTimeField(verbose_name='Slut', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('event', kwargs={'event_id': self.id})


class FoodOrder(models.Model):
    class Meta:
        verbose_name = 'madbestilling'
        verbose_name_plural = 'madbestillinger'

    time = models.DateTimeField(verbose_name='tid')
    lanprofile = models.ForeignKey(LanProfile, on_delete=models.CASCADE, verbose_name='tilmelding')
    order = models.TextField(verbose_name='ordre')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='pris', null=True, blank=True)
    paid = models.BooleanField(default=False, verbose_name='betalt')
    collected = models.BooleanField(default=False, verbose_name='afhentet')

    def __str__(self):
        return self.order

    def get_payment_url(self):
        attrs = {
            'amount': self.price,
            'phone': self.lanprofile.lan.food_phone,
            'comment': 'LAN_MAD|{}'.format(self.pk),
            'lock': '1'
        }
        return 'mobilepay://send?' + urllib.parse.urlencode(attrs)

    def get_payment_qr_url(self):
        attrs = {
            'chs': '300x300',
            'chld': 'M|2',
            'chl': self.get_payment_url(),
            'cht': 'qr'
        }

        return 'https://chart.googleapis.com/chart?' + urllib.parse.urlencode(attrs)
