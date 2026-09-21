from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import HospitalStaff, PatientProfile


class Command(BaseCommand):
    help = 'Seed demo users for production'

    def handle(self, *args, **options):
        # Patient - ravi
        if not User.objects.filter(username='ravi').exists():
            u = User.objects.create_user('ravi', 'ravi@gmail.com', 'ravi123')
            PatientProfile.objects.create(user=u, phone_number='9876543211', aadhaar_last4='1234')
            self.stdout.write(self.style.SUCCESS('Created patient: ravi'))
        else:
            self.stdout.write('Patient ravi already exists')

        # Hospital Staff - Parinitha
        if not User.objects.filter(username='Parinitha').exists():
            u2 = User.objects.create_user('Parinitha', 'parinitha@gmail.com', 'parinitha123')
            HospitalStaff.objects.create(user=u2, staff_name='Parinitha', hospital_name='SDM', is_verified=True)
            self.stdout.write(self.style.SUCCESS('Created staff: Parinitha'))
        else:
            self.stdout.write('Staff Parinitha already exists')

        self.stdout.write(self.style.SUCCESS('Done!'))
