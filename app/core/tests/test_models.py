from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='raj@gmail.com', password='testpass'):
    '''Create a sample user'''
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):

    def test_create_user_with_email_succesful(self):
        """Test creating a new user with email is successful"""
        email = 'brajesh@gmail.com'
        password = 'test123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the new user email is normalized"""
        email = 'brajesh@GMAIL.COM'
        user = get_user_model().objects.create_user(email, 'test123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """ test creating user with no email raises error """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_create_new_superuser(self):
        """ test creating superuser"""
        user = get_user_model().objects.create_superuser(
            'braj@gmail.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        '''Test tag for string representation'''
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Testname'
            )

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        '''Test ingredient for string representation'''
        ingredient = models.Ingredient.objects.create(
            user=sample_user(),
            name='Testname'
            )
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        '''Test recipe for string representation'''
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='steak',
            time_minutes=5,
            price=50.00
            )
        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_uuid(self, mock_uuid):
        '''Test that image is saved in the correct location'''
        uuid = 'test_uuid'

        mock_uuid.return_value = uuid

        file_path = models.recipe_image_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/recipe/{uuid}.jpg'

        self.assertEqual(file_path, exp_path)
