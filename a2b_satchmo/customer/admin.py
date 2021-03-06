from django.contrib import admin
#from django.contrib import databrowse
from django.forms import ModelForm, Textarea, TextInput
from django.views.decorators.cache import never_cache
from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.shortcuts import redirect,render_to_response
from django.utils.translation import ugettext_lazy as _
from django.forms.models import model_to_dict
from django.template import RequestContext
from django.http import  Http404, HttpResponseRedirect
#from django.contrib.sites.models import Site
#from django.contrib.admin.views.main import ChangeList
from a2b_satchmo.customer.forms import *
from a2b_satchmo.customer.models import *
from a2b_satchmo.customer.function_def import *
from satchmo_store.shop.models import Order, OrderItem
from satchmo_store.shop.admin import OrderOptions
from satchmo_store.contact.models import *
from datetime import *
import csv

# Language
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name','lname','charset')
    list_display_links = ('name',)
    #list_editable = ('code','charset')
    list_filter = ['charset']
    
admin.site.register(Language, LanguageAdmin)


class ProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider_name')
    list_display_links = ('provider_name', ) 

admin.site.register(Provider, ProviderAdmin)

class TrunkInline(admin.TabularInline):
    model = Trunk
    fk = 'id_trunk'
    
class TrunkAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('trunkcode', 'trunkprefix', 'providertech', 'id_provider')
        }),
    )
    list_display = ('id_trunk', 'trunkcode', 'trunkprefix','providertech','providerip', 'id_provider')
    
    list_display_links = ('id_trunk', 'trunkcode',) 

admin.site.register(Trunk, TrunkAdmin)


class AlarmAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'periode','type', 'id_trunk')
    list_display_links = ('id', 'name',) 
    inline = [TrunkInline]
admin.site.register(Alarm, AlarmAdmin)

class CardgroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_display_links = ('name', 'description',)

admin.site.register(Cardgroup, CardgroupAdmin)


class CardInline(admin.TabularInline):
    model = Card
    #fk_name = "id"

class CardAdmin(admin.ModelAdmin):
    fieldsets = (
        (_('Customer Information'), {
            #'classes':('collapse',),
            'fields': ('username', 'useralias','uipass','credit','id_group', 'serial',)
        }),
        (_('Personal Information'), {
            'classes':('collapse',),
            'fields': ('lastname','firstname','email','address','city','state','country','zipcode','phone','fax','company_name','company_website',)
        }),
        (_('Customer Status'), {
            'classes':('collapse',),
            'fields': ('typepaid','tariff','id_didgroup','id_timezone','language','currency','status','simultaccess','runservice','creditlimit','credit_notification','notify_email',
                       'email_notification','id_campaign','firstusedate','enableexpire','expirationdate','expiredays','sip_buddy','iax_buddy','mac_addr','inuse',)
        }),
        (_('AUTOREFILL'), {
            'classes':('collapse',),
            'fields': ('autorefill','initialbalance',)
        }),
        (_('Invoice Status'), {
            'classes':('collapse',),
            'fields': ('invoiceday','vat','vat_rn','discount',)
        }),
        (_('TARGET TRAFFIC'), {
            'classes':('collapse',),
            'fields': ('traffic','traffic_target')
        }),
        (_('RESTRICTED NUMBERS'), {
            'classes':('collapse',),
            'fields': ('restriction',)
        }),        
    )
    
    list_display = ('id', 'username', 'useralias','lastname','id_group','ba','tariff','status','language','is_active','action')    
    search_fields = ('useralias', 'username')
    ordering = ('id',)
    list_filter = ['status','id_group','language']
    readonly_fields = ('username','credit','firstusedate')    
    
    def __init__(self, *args, **kwargs):
        super(CardAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = ('username', )
    
    def is_active(self,obj):
        return obj.activated == 't'
    is_active.boolean = True
    is_active.short_description = 'Activated'

    def get_urls(self):
        urls = super(CardAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^view/(?P<id>\d+)$', self.admin_site.admin_view(self.card_detail)),
            (r'^import_cust/$', self.admin_site.admin_view(self.import_cust)),
        )
        return my_urls + urls
    
    def import_cust(self,request):
        opts = Card._meta
        app_label = opts.app_label
        file_exts = ('.csv',)
        rdr = ''        
        if request.method == 'POST':
            #print request.FILES
            form = CustImport(request.POST,request.FILES)
            if form.is_valid():
                header = ['Calldate','Channel','Source','Clid','Destination','Disposition','Duration','AccountCode']
                rdr = csv.reader(request.FILES['csv_file'])
                #rdr.next()
                #for row in rdr:
                #    print row
        else:            
            form = CustImport()
        
        ctx = RequestContext(request, {
        'title': _('Import Customer'),
        'form':form,
        'opts': opts,        
        'model_name': opts.object_name.lower(),
        'app_label': app_label,
        'rdr':rdr,        
        })
        return render_to_response('admin/customer/card/import_cust.html',context_instance=ctx)
    
    def card_detail(self,request, id):
        card = model_to_dict(Card.objects.get(pk=id),exclude=('email_notification', 'loginkey'))
        opts = Card._meta
        app_label = opts.app_label
        card_detail_view_template = 'admin/customer/card/detail_view.html'       
        cxt = {
            'title': _('View %s') % force_unicode(opts.verbose_name),
            'has_change_permission':'yes',
            'opts': opts,
            'model_name': opts.object_name.lower(),
            'app_label': app_label,
            'card':card,
        }        
        return render_to_response(card_detail_view_template , cxt, context_instance=RequestContext(request))
        
    def action(self,form):
        #opts = self.model._meta
        #app_label = opts.app_label
        #return '<a href=\"/admin/%s/view/%d/\" target="_blank">view</a>' % (opts.object_name.lower(),form.id)
        return '<a href="view/%s" >view</a>' % (form.id)
    action.allow_tags = True

admin.site.register(Card, CardAdmin)
#databrowse.site.register(Card)

class SpeeddialAdmin(admin.ModelAdmin):
    form = SpeeddiaForm
    list_display = ('creationdate', 'acc_no','name','phone','speeddial')
    list_display_links = ('name',)

admin.site.register(Speeddial, SpeeddialAdmin)


class CardHistoryAdmin(admin.ModelAdmin):    
    list_display = ('customer_acc_no','datecreated','description',)
    change_list_template = 'admin/customer/cardhistory/change_list.html'
    def __init__(self, *args, **kwargs):
        super(CardHistoryAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )
    
    def get_urls(self):
        urls = super(CardHistoryAdmin, self).get_urls()
        my_urls = patterns('',(r'^admin/customer/cardhistory/$', self.admin_site.admin_view(self.changelist_view)),
        )
        return my_urls + urls

    def queryset(self, request):
        kwargs = {}
        kwargs = card_history_status_common_fun(request,date_field_name='datecreated',form_require="no")
        qs = super(CardHistoryAdmin, self).queryset(request)
        return qs.filter(**kwargs).order_by('-datecreated')

    def changelist_view(self, request,  extra_context=None):
        if request.method == 'POST':
            form = card_history_status_common_fun(request,date_field_name='datecreated',form_require="yes")
        else:            
            form = CardHistoryForm(initial={})
        ctx = {
            'form': form,
            'has_add_permission': '',
        }
        return super(CardHistoryAdmin, self).changelist_view(request,  extra_context=ctx)
     
admin.site.register(CardHistory, CardHistoryAdmin)

class StatusLogAdmin(admin.ModelAdmin):    
    list_display = ('id_card','customer_acc_no','last_name','status','updated_date',)
    list_filter = ['status',]
    change_list_template = 'admin/customer/statuslog/change_list.html'
    
    def __init__(self, *args, **kwargs):
        super(StatusLogAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    def get_urls(self):
        urls = super(StatusLogAdmin, self).get_urls()
        my_urls = patterns('',(r'^admin/customer/statuslog/$', self.admin_site.admin_view(self.changelist_view)),
        )
        return my_urls + urls

    def queryset(self, request):
        kwargs = {}
        kwargs = card_history_status_common_fun(request,date_field_name='updated_date',form_require="no")
        qs = super(StatusLogAdmin, self).queryset(request)
        return qs.filter(**kwargs).order_by('-updated_date')

    def changelist_view(self, request,  extra_context=None):
        if request.method == 'POST':
            form = card_history_status_common_fun(request,date_field_name='updated_date',form_require="yes")
        else:
            form = CardHistoryForm(initial={})
        ctx = {
            'form': form,
            'has_add_permission': '',
        }
        return super(StatusLogAdmin, self).changelist_view(request,  extra_context=ctx)

admin.site.register(StatusLog, StatusLogAdmin)

class CallAdmin(admin.ModelAdmin):
    list_display = ('starttime','src','dnid','calledstation','destination_name' ,'card_id_link','id_trunk','buy','call_charge','duration','terminatecauseid','sipiax')
    list_filter = ['starttime', 'calledstation']    
    #search_fields = ('card_id','dst', 'src','starttime',)
    date_hierarchy = ('starttime')
    ordering = ('-id',)
    #list_editable = ['src']
    change_list_template = 'admin/customer/call/change_list.html'        
    
    def __init__(self, *args, **kwargs):
        super(CallAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )    
    
    def get_urls(self):
        urls = super(CallAdmin, self).get_urls()
        my_urls = patterns('',(r'^admin/customer/call/$', self.admin_site.admin_view(self.changelist_view)),                             
        )        
        return my_urls + urls
        
    def queryset(self, request):
        kwargs = {}
        kwargs = call_record_common_fun(request,form_require="no")        
        qs = super(CallAdmin, self).queryset(request)
        return qs.select_related('prefix__destination', 'destination').filter(**kwargs).order_by('-starttime')
    
    def changelist_view(self, request,  extra_context=None):        
        if request.method == 'POST':            
            form = call_record_common_fun(request,form_require="yes")                                               
        else:
            #result = 'min'
            form = SearchForm(initial={'currency': config_value('base_currency').upper(),'phone_no_type':1,'show':0,'result':'min'})                
        ctx = {
            'form': form,            
            'has_add_permission': '',
        }
        return super(CallAdmin, self).changelist_view(request,  extra_context=ctx)
admin.site.register(Call, CallAdmin)


class CalleridAdmin(admin.ModelAdmin):
    form = CalleridForm
    list_display = ('cid','customer_acc_no','customer_name','is_active')
    #prepopulated_fields = {"cid": ("cid",)}
    radio_fields = {"activated": admin.HORIZONTAL}    
    search_fields = ('cid', 'id_cc_card')
    ordering = ('id',)
    actions = ['make_active_deactive']    
    def make_active_deactive(self, request, queryset):
        rows_updated = 0
        for i in queryset:
            callerid = Callerid.objects.values('activated').get(id=i.id)           
            if callerid['activated'] == 't':
                Callerid.objects.values('activated').filter(id=i.id).update(activated='f')
                rows_updated = rows_updated + 1
            else:
                Callerid.objects.values('activated').filter(id=i.id).update(activated='t')
                rows_updated = rows_updated + 1
                
        if rows_updated == 1:
            message_bit = "1 caller id was"
        else:
            message_bit = "%s caller ids were" % rows_updated
        self.message_user(request, "%s successfully updated." % message_bit)
    make_active_deactive.short_description = "Mark selected Caller ID as Active/Deactive"
    
    def is_active(self,obj):
        return obj.activated == 't'
    is_active.boolean = True
    is_active.short_description = 'Activated'

admin.site.register(Callerid, CalleridAdmin)

#Config Group List
class ConfigGroupAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('group_title','group_description'),
        }),
    )
    list_display = ('group_title','group_description')    
    search_fields = ('group_title', 'group_description')    
    ordering = ('id',)
admin.site.register(ConfigGroup, ConfigGroupAdmin)

#Admin side Config Model
class ConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('config_group_title','config_title','config_key','config_value','config_description',),
        }),
    )    
    form = ConfigForm    
    list_display = ('config_title','config_key','config_value','config_description','config_group_title',)
    search_fields = ('config_title', 'config_key','config_description')
    #readonly_fields = ('config_title','config_key','config_description',)
    list_filter = ['config_group_title']
    ordering = ('config_group_title',)        
    #formfield_overrides = {
    #    models.CharField: {'widget': TextInput(attrs={'readonly':'readonly',})},
    #    models.TextField: {'widget': Textarea(attrs={'readonly':'readonly',})},
    #}

admin.site.register(Config, ConfigAdmin)

#Admin side  IaxBuddies Model
class  IaxBuddiesAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('id_cc_card','name','accountcode','regexten','callerid','cid_number','amaflags','secret','qualify',
                       'disallow','allow','host','context','defaultip','language','port','regseconds','ipaddr',
                       'mohsuggest','auth','setvar','type','permit','deny','trunk','dbsecret','regcontext','sourceaddress','mohinterpret',
                       'inkeys','outkey','sendani','fullname','maxauthreq','encryption','transfer',
                       'jitterbuffer','forcejitterbuffer','codecpriority','qualifysmoothing','qualifyfreqok','qualifyfreqnotok',
                       'timezone','adsi','requirecalltoken','maxcallnumbers','maxcallnumbers_nonvalidated',
                       ),
        }),
    )
    list_display = ('card_holder_name','name','accountcode','secret','callerid','context','default_ip')
    search_fields = ('name',)
    list_display_links = ('name',)
    ordering = ('name',)
    """
    #form = ConfigForm
    list_filter = ['config_group_title']
    ordering = ('config_group_title',)
    """

admin.site.register(IaxBuddies,  IaxBuddiesAdmin)

#Admin side SipBuddies Model
class SipBuddiesAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('id_cc_card','name','accountcode','regexten','callerid','cid_number','amaflags','secret','qualify',
                       'disallow','allow','host','context','defaultip','language','port','regseconds','ipaddr',
                       'mohsuggest','auth','setvar','type','permit','deny','username','md5secret','nat','dtmfmode',
                       'canreinvite','callgroup','fromuser','fromdomain','insecure','mailbox','mask','pickupgroup',
                       'restrictcid','rtptimeout','rtpholdtimeout','musiconhold','cancallforward','defaultuser','subscribemwi',
                       'vmexten','callingpres','usereqphone','incominglimit','subscribecontext','musicclass',
                       'allowtransfer','autoframing','maxcallbitrate','outboundproxy','regserver','rtpkeepalive',
            ),
        }),
    )
    list_display = ('card_holder_name','name','accountcode','secret','callerid','context','default_ip')
    search_fields = ('name',)
    list_display_links = ('name',)
    ordering = ('name',)
    """
    #form = ConfigForm
    list_filter = ['config_group_title']
    ordering = ('config_group_title',)
    """

admin.site.register(SipBuddies, SipBuddiesAdmin)


class OrderExtend:
    def order_sku(self):
        allsku = ''
        for item in self.orderitem_set.all():
            allsku += "%s<br />" % item.product.sku
        return allsku
    order_sku.allow_tags = True
    order_sku.short_description = "Order SKUs"

Order.__bases__ += (OrderExtend,)

admin.site.unregister(Order)

class CustomOrderAdmin(OrderOptions):
    list_display = ('id', 'order_sku', 'contact', 'time_stamp',
                    'order_total', 'balance_forward', 'status',
                    'invoice', 'packingslip')

admin.site.register(Order, CustomOrderAdmin)

