from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


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
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {'title': 'Chicken Tikka', 'tags': [new_tag.id]}

        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        '''test updating a recipe with put'''
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')
        payload = {'title': 'Spaghetti', 'time_minutes': 50, 'price': 100}

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])

        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)
