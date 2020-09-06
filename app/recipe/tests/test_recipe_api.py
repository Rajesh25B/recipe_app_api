import tempfile
import os

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

from PIL import Image

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    '''Return url for recipe model image field'''
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    '''Return the recipe detail URL'''
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main Course'):
    '''Creating and returning sample tag'''
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinomen'):
    '''Creating and returning a sample ingredient'''
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 50.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    '''Test unauthenticated recipe API access'''
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test that authentication is required'''
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    ''' Test authenticated recipe API access'''
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'rajesh@gmail.com',
            'randompassword'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test retrieving a list of recipes by creating two recipes'''
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        '''Test retrieving recipes for user'''
        user2 = get_user_model().objects.create_user(
            'molly155@gmail.com',
            'password123'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        '''Test viewing a recipe detail'''
        recipe = sample_recipe(user=self.user)

        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)

        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        '''Test creating recipe'''
        payload = {
            'title': 'Basic Recipe',
            'time_minutes': 10,
            'price': 100
            }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Retrieve the created recipe from our Recipe Model
        recipe = Recipe.objects.get(id=res.data['id'])
        # loop through the payload keys to check the payload values equal to
        # recipe model values
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        '''Test creating recipe with tags'''

        tag1 = sample_tag(user=self.user, name='Sample1')
        tag2 = sample_tag(user=self.user, name='Sample2')

        payload = {
            'title': 'Recipe with tags',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 10,
            'price': 100
            }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        '''Test creating recipe with ingredients'''
        ingredient1 = sample_ingredient(user=self.user, name='Ingredient 1')
        ingredient2 = sample_ingredient(user=self.user, name='Ingredient 2')

        payload = {
            'title': 'Sample Attachment',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 15,
            'price': 30
            }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        '''Test updating a recipe with patch'''
        recipe = sample_recipe(user=self.user)  # Created a sample recipe
        recipe.tags.add(sample_tag(user=self.user))  # assigned tag

        new_tag = sample_tag(user=self.user, name='Curry')  # Added new tag

        # new recipe payload
        payload = {'title': 'Chicken Tikka', 'tags': [new_tag.id]}

        url = detail_url(recipe.id)  # Added url and response
        self.client.patch(url, payload)

        recipe.refresh_from_db()  # refresh the db with new_tag values

        # Assert existing recipe title with payload title
        self.assertEqual(recipe.title, payload['title'])
        # Retrieve all tags assigned with payload tags
        tags = recipe.tags.all()
        # Check length of the tags = 1
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        '''test updating a recipe with put'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {'title': 'Spaghetti', 'time_minutes': 50, 'price': 100}

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])

        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        # Create sample user and force authenticate
        self.user = get_user_model().objects.create_user(
            'testimage@mail.com',
            'testpass'
            )
        self.client.force_authenticate(self.user)
        # Create a sample recipe for testing uploading our image to
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        ''' Opposite for setUp'''
        # we need to keep clean our system by removing
        # all the tests that we created
        self.recipe.image.delete()
        # This delete method deletes if any image already exists

    def test_upload_valid_image_to_recipe(self):
        '''Test uploading a valid image to recipe'''
        url = image_upload_url(self.recipe.id)

        # NamedTemporaryFile creates a named temporary file
        # in the system at a random location
        # Create a temporary file, write an image to that file,
        # upload that file through the API
        # and run some assertions that it uploaded correctly
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')

            ntf.seek(0)

            res = self.client.post(url, {'image': ntf}, format='multipart')

            self.recipe.refresh_from_db()

            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn('image', res.data)
            self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_image_to_recipe(self):
        '''Test uploading an invalid image'''
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'Notanimage'},
                               format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filer_recipe_by_tags(self):
        '''Test returning recipes by filtering tags'''
        # Create 3 recipes and 2 tags
        recipe1 = sample_recipe(user=self.user, title='R1')
        recipe2 = sample_recipe(user=self.user, title='R2')
        recipe3 = sample_recipe(user=self.user, title='R3')

        tag1 = sample_tag(user=self.user, name='T1')
        tag2 = sample_tag(user=self.user, name='T2')

        # Assign tags to recipes
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        # Make a request for tag1 & tag2 in recipe db.
        res = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag1.id}, {tag2.id}'}
            )

        # Serialize the recipes
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        # Check the serialized recipes data exist in response returned
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        '''Test returning recipes by filtering ingredients'''
        recipe1 = sample_recipe(user=self.user, title='R1')
        recipe2 = sample_recipe(user=self.user, title='R2')
        recipe3 = sample_recipe(user=self.user, title='R3')

        ingredient1 = sample_ingredient(user=self.user, name='I1')
        ingredient2 = sample_ingredient(user=self.user, name='I2')

        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        res = self.client.get(
            RECIPES_URL,
            {'ingredients': f'{ingredient1.id}, {ingredient2.id}'}
            )
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
