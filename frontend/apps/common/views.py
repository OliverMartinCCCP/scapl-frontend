# -*- coding: UTF-8 -*-
from django.shortcuts import render


def index(request):
    return render(request, 'index.html')


def home(request):
    return render(request, 'base.html')
