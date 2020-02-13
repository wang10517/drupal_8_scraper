# -*- coding: utf-8 -*-
import scrapy
import csv
import random
import logging

class convention(object):
    def __init__(self, d):
        self.__dict__ = d

module_names = ['project/admin_devel', 'project/admin_menu', 'project/admin_menu_toolbar', 'project/admin_views', 'project/advagg', 'project/backup_migrate', 'project/boost', 'project/calendar', 'project/captcha', 'project/chestnut', 'project/chestnut_blog', 'project/chestnut_core', 'project/chestnut_ldap', 'project/chestnut_module', 'project/chestnut_press_release', 'project/chestnut_profile', 'project/chestnut_promos', 'project/chestnut_rotator', 'project/chestnut_text', 'project/chestnut_video', 'project/ckeditor', 'project/ckeditor_abbreviation', 'project/clone', 'project/colorbox', 'project/context', 'project/context_ui', 'project/devel', 'project/diff', 'project/draggableviews', 'project/expire', 'project/extlink', 'project/features', 'project/field_collection', 'project/field_group', 'project/follow', 'project/globalredirect', 'project/gmap', 'project/gmap_fields', 'project/gmap_location', 'project/googleanalytics', 'project/iamohio_members', 'project/imce', 'project/imce_mkdir', 'project/jquery_update', 'project/ldap_authentication', 'project/ldap_servers', 'project/ldap_user', 'project/libraries', 'project/linkchecker', 'project/linkit', 'project/location', 'project/location_cck', 'project/location_entity', 'project/menu_block', 'project/module_filter', 'project/multiupload_filefield_widget', 'project/multiupload_imagefield_widget', 'project/node_reference', 'project/oht_health_check', 'project/ohtech_calendar', 'project/password_policy', 'project/pathauto', 'project/phone', 'project/recaptcha', 'project/redirect', 'project/references', 'project/security_review', 'project/strongarm', 'project/text_resize', 'project/token', 'project/user_reference', 'project/uuid', 'project/views', 'project/views_bootstrap', 'project/views_bulk_operations', 'project/views_slideshow', 'project/views_slideshow_cycle', 'project/webform', 'project/webform_validation']
handle_httpstatus_list = [404,403]
error_code = convention({
"BLOCKED" : 403,
"NOT_FOUND" : 404
})

status_mesg = convention({
    "BLOCKED" : "Blocked",
    "NOT_FOUND" : "Not found",
    "FOUND" : "Found"
})
issue_mesg = convention({
    "PLACEHOLDER" : "Placeholder Site",
    "NOT_SUPPORTED" : "Not supported anymore",
    "ALREADY_INCLUDED" : "Already included in Drupal8 Core",
    "AVAILABLE" : "Available",
    "DEV_VERSION" : "Dev version only",
    "INAVAILALBE" : "Not available yet"
})
PH = 'N/A'
TYPE_CUSTOM = 'custom'
TYPE_CONTRIB = 'contrib'
DESIRED_VERSION = '8'

# Collection of keywords for classficiation purpose 
custom_keywords = ["chestnut", "iam", "ohtech","oht","oar"]
place_holder_keywords = ["place holder","placeholder"]
unsupported_keywords = [ "Not needed","Obsolete", "obsolete","Unsupported","unsupported", "deprecated", "Deprecated" ,"not supported"]
inclusion_hint = 'This module has been included with Drupal 8 core.'

## Helper function for the spider class

class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["www.drupal.org"]
    start_urls = [
        'https://www.drupal.org/',
    ]
    rotate_user_agent = True
    def parse(self, response):
        for mod in module_names:
            ## Determine the type of the module
            ## if custom, skip searching
            is_custom = False
            for custom_keyword in custom_keywords:
                if custom_keyword in mod:
                    item = {}
                    item['name'] = mod.split('/')[-1]
                    item['title'] = PH
                    item['type'] = TYPE_CUSTOM
                    item['status'] = PH
                    item['issue'] = PH
                    item['last update'] = PH
                    item['description'] = PH
                    item['link'] =PH
                    is_custom = True
                    yield item
                    break
            if not is_custom:
                yield scrapy.Request(response.urljoin(mod), callback=self.parse_mod_page,meta={'machine_name':mod, 'url':'https://www.drupal.org/%s'%(mod)})

    def parse_mod_page(self, response):
        machine_name = response.meta['machine_name'].split('/')[-1]
        searched_url = response.meta['url']
        item = {}
        # if not 200
        if response.status in handle_httpstatus_list:
                if response.status == error_code.NOT_FOUND:
                    item['name'] = machine_name
                    item['title'] = PH
                    item['type'] = TYPE_CONTRIB
                    item['status'] = status_mesg.NOT_FOUND
                    item['issue'] = PH
                    item['last update'] = PH
                    item['description'] = PH
                    item['link'] =searched_url
                elif response.status == error_code.BLOCKED:
                    item['name'] = machine_name
                    item['title'] = PH
                    item['type'] = TYPE_CONTRIB
                    item['status'] = status_mesg.BLOCKED
                    item['issue'] = PH
                    item['last update'] = PH
                    item['description'] = PH
                    item['link'] =searched_url
                yield item
        else:
            title = response.css("#page-subtitle").xpath("text()").get()
            description = response.css(".field-type-text-with-summary p").xpath("text()").get()
            if description.isspace():
                description = response.css(".field-type-text-with-summary p")[1].xpath("text()").get()
            last_update = response.css(".submitted time").xpath("text()").getall()[1]
            # When the site is merely a placeholder
            for keyword in place_holder_keywords:
                if keyword in description:
                    item['name'] = machine_name
                    item['title'] = title
                    item['type'] = TYPE_CONTRIB
                    item['status'] = status_mesg.FOUND
                    item['issue'] = issue_mesg.PLACEHOLDER
                    item['last update'] = last_update
                    item['description'] = description
                    item['link'] =searched_url
                    new_url = response.css(".field-type-text-with-summary a::attr(href)").extract_first()
                    new_machine_name = new_url.split("/")[-1]
                    ## yield item
                    self.logger.info('Redirecting to %s at %s',new_machine_name, new_url)
                    yield scrapy.Request(new_url, callback=self.parse_mod_page,meta={'machine_name':new_machine_name, 'url':new_url})
                    yield item
                    return
            
            # Check if still supported
            project_status = response.css(".project-info li").xpath("text()").getall()
            for keyword in unsupported_keywords:
                if keyword in project_status:
                    item['name'] = machine_name
                    item['title'] = title
                    item['type'] = TYPE_CONTRIB
                    item['status'] = status_mesg.FOUND
                    item['issue'] = issue_mesg.NOT_SUPPORTED
                    item['last update'] = last_update
                    item['description'] = description
                    item['link'] =searched_url
                    yield item
                    return
            
            #Check if already included in drupal8 core
            help_text = response.css(".help").xpath("text()").getall()
            if help_text:
                for t in help_text:
                    if inclusion_hint in t:
                        item['name'] = machine_name
                        item['title'] = title
                        item['type'] = TYPE_CONTRIB
                        item['status'] = status_mesg.FOUND
                        item['issue'] = issue_mesg.ALREADY_INCLUDED
                        item['last update'] = last_update
                        item['description'] = description
                        item['link'] =searched_url
                        yield item
                        return 
                    for key in unsupported_keywords:
                        if key in t:
                            item['name'] = machine_name
                            item['title'] = title
                            item['type'] = TYPE_CONTRIB
                            item['status'] = status_mesg.FOUND
                            item['issue'] = issue_mesg.NOT_SUPPORTED
                            item['last update'] = last_update
                            item['description'] = description
                            item['link'] =searched_url
                            yield item
                            return
            #Check to see if it is available yet
            ava_versions = response.css(".view-content .views-field-field-release-version a").xpath("text()").getall()
            dev_versions = response.css(".view-footer .release a").xpath("text()").getall()
            for ava_v in ava_versions:
                if DESIRED_VERSION in ava_v:
                    item['name'] = machine_name
                    item['title'] = title
                    item['type'] = TYPE_CONTRIB
                    item['status'] = status_mesg.FOUND
                    item['issue'] = issue_mesg.AVAILABLE
                    item['last update'] = last_update
                    item['description'] = description
                    item['link'] =searched_url
                    yield item
                    return
            for dev_v in dev_versions:
                if DESIRED_VERSION in dev_v:
                    item['name'] = machine_name
                    item['title'] = title
                    item['type'] = TYPE_CONTRIB
                    item['status'] = status_mesg.FOUND
                    item['issue'] = issue_mesg.DEV_VERSION
                    item['last update'] = last_update
                    item['description'] = description
                    item['link'] =searched_url
                    yield item
                    return
            
            item['name'] = machine_name
            item['title'] = title
            item['type'] = TYPE_CONTRIB
            item['status'] = status_mesg.FOUND
            item['issue'] = issue_mesg.INAVAILALBE
            item['last update'] = last_update
            item['description'] = description
            item['link'] =searched_url
            yield item
    
