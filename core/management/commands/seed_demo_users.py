from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from core.models import HospitalStaff, PatientProfile


class Command(BaseCommand):
    help = 'Seed demo users for production'

    def handle(self, *args, **options):
        # Patient - ravi
        user, created = User.objects.get_or_create(
            username='ravi',
            defaults={'email': 'ravi@gmail.com'}
        )
        if created:
            user.set_password('ravi123')
            user.save()
        if not hasattr(user, 'patient_profile'):
            PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    'age': 28,
                    'district': 'Bengaluru Urban',
                    'economic_status': 'BPL',
                    'has_ration_card': True,
                    'has_aadhaar': True,
                    'aadhaar_last4': '1234',
                    'disease_type': 'None',
                    'phone_number': '9876543211',
                }
            )
            self.stdout.write(self.style.SUCCESS('Created patient: ravi'))
        else:
            self.stdout.write('Patient ravi already exists')

        # Hospital Staff - Parinitha
        user2, created2 = User.objects.get_or_create(
            username='Parinitha',
            defaults={'email': 'parinitha@gmail.com'}
        )
        if created2:
            user2.set_password('parinitha123')
            user2.save()
        if not hasattr(user2, 'hospital_staff'):
            HospitalStaff.objects.get_or_create(
                user=user2,
                defaults={
                    'staff_name': 'Parinitha',
                    'hospital_name': 'SDM',
                    'license_number': 'SDM001',
                    'is_verified': True,
                }
            )
            self.stdout.write(self.style.SUCCESS('Created staff: Parinitha'))
        else:
            self.stdout.write('Staff Parinitha already exists')

        self.stdout.write(self.style.SUCCESS('Done!'))
