from django.shortcuts import render, redirect
from django.conf import settings
from meta.views import Meta 


def home(request):
    meta = Meta(
        title='Convert & Edit tools for  PDF, Docs & Images',
        description='Online Convert and Edit Tools for PDF Docs Excel Image PowerPoint HTML etc. files in clicks',
        keywords = ['word', 'image', 'powerpoint', 'power-point', 'excel'],
        og_title='iLovePdfConverterOnline - Homepage',
        og_description='Online Convert and Edit Tools for PDF Docs Excel Image PowerPoint HTML etc. files in clicks', 
        # ... other meta tags as needed
    ) 

    context = {'meta': meta}
    return render(request, 'core/home.html', context)


def about(request):
    meta = Meta(
        title='iLovePdfConverterOnline - About',
        description='Aboust us page for iLovePdfConverterOnline.com. We provide convert tools for PDF to convert into Word, Image, PowerPoint, Excel file types and also reverser conversion tools are also available to convert Word, Image, PowerPoint, Excel, HTML to PDF file type. ilovepdfconveronline.com also provide some extrad daily office PDF documentation tools Merge PDF, Split PDF, Compress PDF, Rotate PDF, and etc. to provide you husstle free documentation work and make your day. ',
        author='iLovePdfConverterOnline',
        og_title='iLovePdfConverterOnline - About',
        og_description='Aboust us page for iLovePdfConverterOnline.com. We provide convert tools for PDF.', 
        # ... other meta tags as needed
    ) 

    context = {'meta': meta}
    return render(request, 'core/about.html', context)

def contactus(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Contact Us',
        description='Contact Us page for iLovePdfConverterOnline.com.',
        author='iLovePdfConverterOnline',
        og_title='iLovePdfConverterOnline - Contact Us',
        og_description='Contact Us page for iLovePdfConverterOnline.com.', 
        # ... other meta tags as needed
    ) 

    context = {'meta': meta}
    return render(request, 'core/contactus.html', context)

def termscondition(request):
    meta = Meta(
        title='iLovePdfConverterOnline - Terms & Condition',
        description='Terms & Condition page of iLovePdfConverterOnline.com.',
        author='iLovePdfConverterOnline',
        og_title='iLovePdfConverterOnline - Terms & Condition',
        og_description='Terms & Condition page for iLovePdfConverterOnline.com.', 
        # ... other meta tags as needed
    ) 

    context = {'meta': meta}
    return render(request, 'core/terms_and_condition.html', context)

