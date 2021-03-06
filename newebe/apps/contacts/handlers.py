import datetime
import logging

from tornado.web import asynchronous
from tornado.escape import json_decode
from tornado.websocket import WebSocketHandler

from newebe.lib.slugify import slugify
from newebe.lib.http_util import ContactClient

from newebe.apps.profile.models import UserManager
from newebe.apps.contacts.models import Contact, ContactManager, ContactTag, \
                               STATE_WAIT_APPROVAL, STATE_ERROR, \
                               STATE_TRUSTED, STATE_PENDING
from newebe.apps.core.handlers import NewebeAuthHandler, NewebeHandler


# Template handlers for contact pages.
logger = logging.getLogger(__name__)

# Long polling queue
websocket_clients = []


class ContactPublishingHandler(WebSocketHandler):
    '''
    Handler that manages websocket connections
    TODO: Set authentication there.
    '''

    def open(self):
        '''
        Add a websocket client to the websocket pool.
        '''
        websocket_clients.append(self)
        logger.info("New web socket client")

    def on_close(self):
        '''
        Remove leaving websocket client from the websocket pool.
        '''
        websocket_clients.remove(self)
        logger.info("A web socket client left")


class ContactUpdateHandler(NewebeHandler):

    def put(self):
        '''
        When a put request is received, contact data are expected. If contact
        key is one of the trusted contact key, its data are updated with
        received ones.
        '''

        data = self.get_body_as_dict(["key", "url", "name", "description"])

        if data:
            key = data["key"]

            contact = ContactManager.getTrustedContact(key)
            if contact:
                contact.url = data["url"]
                contact.description = data["description"]
                contact.name = data["name"]
                contact.tags = data["tags"]
                contact.save()

                self.create_modify_activity(contact, "modifies", "profile")
                self.return_success("Contact successfully modified.")

            else:
                self.return_failure(
                        "No contact found corresponding to given contact", 404)

        else:
            self.return_failure("Empty data or missing field.")


class ContactPictureUpdateHandler(NewebeHandler):

    def put(self):
        '''
        When a put request is received, contact thumbnail is expected.
        If contact key is one of the trusted contact key, its data are updated
        with received ones.
        '''

        picfile = self.request.files['small_picture'][0]
        contactKey = self.get_argument("key")

        if picfile and contactKey:
            contact = ContactManager.getTrustedContact(contactKey)

            if contact:
                contact.save()
                contact.put_attachment(content=picfile["body"],
                                       name="small_picture.jpg")
                contact.save()
                self.return_success("Contact picture successfully modified.")
            else:
                self.return_failure(
                    "No contact found corresponding to given contact", 404)

        else:
            self.return_failure("Empty data or missing field.")


class ContactsPendingHandler(NewebeAuthHandler):
    '''
     * GET : retrieve only contacts that have not approved your contact
              request or  contacts that returned an error.
    '''

    def get(self):
        '''
        Retrieve whole contact list at JSON format.
        '''

        contacts = ContactManager.getPendingContacts()

        self.return_documents(contacts)


class ContactsRequestedHandler(NewebeAuthHandler):
    '''
     * GET : contacts that wait for approval.
    '''

    def get(self):
        '''
        Retrieve whole contact list at JSON format.
        '''

        contacts = ContactManager.getRequestedContacts()

        self.return_documents(contacts)


class ContactsTrustedHandler(NewebeAuthHandler):
    '''
     * GET : retrieve only contacts that are trusted by newebe owner
    '''

    def get(self):
        '''
        Retrieve whole contact list at JSON format.
        '''

        contacts = ContactManager.getTrustedContacts()

        self.return_documents(contacts)


class ContactHandler(NewebeAuthHandler):
    '''
    Resource to manage specific contacts.
    GET: Gets a contact for a given slug.
    PUT: Confirm contact request.
    DELETE: Deletes contact corresponding to given slug.
    '''

    def get(self, slug):
        '''
        Retrieves contact corresponding to slug at JSON format.
        '''

        contact = ContactManager.getContact(slug)

        self.return_one_document_or_404(contact, "Contact does not exist.")

    @asynchronous
    def put(self, slug):
        '''
        Confirm contact request or update tag data.
        '''

        data = self.get_body_as_dict(["state"])
        state = data["state"]
        tags = data.get("tags", None)
        self.contact = ContactManager.getContact(slug)

        if self.contact:
            if self.contact.state != STATE_TRUSTED and state == STATE_TRUSTED:
                self.contact.state = STATE_TRUSTED
                self.contact.save()

                user = UserManager.getUser()
                data = user.asContact().toJson(localized=False)

                try:
                    client = ContactClient()
                    client.post(self.contact, "contacts/confirm/", data,
                                self.on_contact_response)
                except:
                    self.contact.state = STATE_ERROR
                    self.contact.save()
                    self.return_failure(
                        "Error occurs while confirming contact.")

            elif tags != None:
                self.contact.tags = tags
                self.contact.save()
                self.return_success("Contact tags updated.")

            else:
                self.return_success("Nothing to change.")

        else:
            self.return_failure("Contact to confirm does not exist.")

    def on_contact_response(self, response, **kwargs):
        '''
        Check contact response and set contact status depending on this
        response.
        '''

        try:
            incomingData = response.body
            newebeResponse = json_decode(incomingData)
            if not newebeResponse["success"]:
                raise Exception()

            # idea: try to save picture to disk then call file.read()
            # to add file data.
            #user = UserManager.getUser()
            #picture = user.fetch_attachment("small_picture.jpg")
            #self.send_files_to_contact(self.contact,
            #    "contact/update-profile/picture/",
            #    fields={"key": user.key},
            #    files=[("small_picture", "small_picture.jpg", picture)]
            #)

            self.return_success("Contact trusted.")
        except:
            self.contact.state = STATE_ERROR
            self.contact.save()
            self.return_failure("Error occurs while confirming contact.")

    def delete(self, slug):
        '''
        Deletes contact corresponding to slug.
        '''

        contact = ContactManager.getContact(slug)
        if contact:
            contact.delete()
            return self.return_success("Contact has been deleted.")
        else:
            self.return_failure("Contact does not exist.")


class ContactsHandler(NewebeAuthHandler):
    '''
    This is the resource for contact data management. It allows :
     * GET : retrieves all contacts data.
     * POST : creates a new contact.
    '''

    def get(self):
        '''
        Retrieves whole contact list at JSON format.
        '''
        contacts = ContactManager.getContacts()
        self.return_documents(contacts)

    @asynchronous
    def post(self):
        '''
        Creates a new contact from web client data
        (contact object at JSON format). And send a contact request to the
        newly created contact. State of contact is set to PENDING.
        '''

        logger = logging.getLogger("newebe.contact")

        data = self.get_body_as_dict(["url"])

        if data:
            url = data["url"]
            owner = UserManager.getUser()

            if owner.url != url:
                slug = slugify(url)

                self.contact = Contact(
                  url=url,
                  slug=slug
                )
                self.contact.save()

                try:
                    data = UserManager.getUser().asContact().toJson()

                    client = ContactClient()
                    client.post(self.contact, "contacts/request/",
                                data, self.on_contact_response)

                except Exception:
                    import traceback
                    logger.error("Error on adding contact:\n %s" %
                        traceback.format_exc())

                    self.contact.state = STATE_ERROR
                    self.contact.save()

            else:
                return self.return_failure(
                        "Wrong data. Url is same as owner URL.", 400)
        else:
            return self.return_failure(
                    "Wrong data. Contact has not been created.", 400)

    def on_contact_response(self, response, **kwargs):
        '''
        On contact response, checks if no error occured. If error occured,
        it changes the contact status from Pending to Error.
        '''

        try:
            newebeResponse = json_decode(response.body)
            if not "success" in newebeResponse or \
               not newebeResponse["success"]:
                self.contact.state = STATE_ERROR
                self.contact.save()

        except:
            import traceback
            logger.error("Error on adding contact, stacktrace :\n %s" %
                    traceback.format_exc())

            self.contact.state = STATE_ERROR
            self.contact.save()

        finally:
            return self.return_one_document(self.contact, 201)


class ContactRetryHandler(NewebeAuthHandler):
    '''
    This handler allows to resend contact request to a contact that have
    already received contact request.
    * POST: Send a new contact request to given contact if its state is
    set as Pending or Error.
    '''

    @asynchronous
    def post(self, slug):
        '''
        When post request is received, contact of which slug is equal to
        slug is retrieved. If its state is Pending or Error, the contact
        request is send again.
        '''

        logger = logging.getLogger("newebe.contact")

        self.contact = ContactManager.getContact(slug)
        owner = UserManager.getUser()

        if self.contact and self.contact.url != owner.url:
            try:
                data = owner.asContact().toJson()

                client = ContactClient()
                client.post(self.contact, "contacts/request/", data,
                            self.on_contact_response)

            except Exception:
                import traceback
                logger.error("Error on adding contact:\n %s" %
                        traceback.format_exc())

                self.contact.state = STATE_ERROR
                self.contact.save()

        else:
            self.return_failure("Contact does not exist", 404)

    def on_contact_response(self, response, **kwargs):

        if response.code != 200:
            self.contact.state = STATE_ERROR
            self.contact.save()

        else:
            self.contact.state = STATE_PENDING
            self.contact.save()

        self.return_one_document(self.contact)


class ContactPushHandler(NewebeHandler):
    '''
    This is the resource for contact request. It allows :
     * POST : asks for a contact authorization.
    '''

    def post(self):
        '''
        Create a new contact from sent data (contact object at JSON format).
        Sets its status to Wait For Approval
        '''
        data = self.get_body_as_dict(expectedFields=["url"])

        if data:
            url = data["url"]
            owner = UserManager.getUser()

            if owner.url != url:
                slug = slugify(url)

                contact = ContactManager.getContact(slug)
                owner = UserManager.getUser()

                if contact is None:
                    contact = Contact(
                        name=data["name"],
                        url=url,
                        slug=slug,
                        key=data["key"],
                        state=STATE_WAIT_APPROVAL,
                        requestDate=datetime.datetime.utcnow(),
                        description=data["description"]
                    )
                    contact.save()

                contact.state = STATE_WAIT_APPROVAL
                contact.save()

                for websocket_client in websocket_clients:
                    websocket_client.write_message(contact.toJson())

                self.return_success("Request received.")

            else:
                self.return_failure("Contact and owner have same url.")

        else:
            self.return_failure("Sent data are incorrects.")


class ContactConfirmHandler(NewebeHandler):
    '''
    This is the resource for contact confirmation. It allows :
     * POST : confirm a contact and set its state to TRUSTED.
    '''

    def post(self):
        '''
        Updates contact from sent data (contact object at JSON format).
        Sets its status to Trusted.
        '''
        data = self.get_body_as_dict(expectedFields=["url", "key", "name"])

        if data:
            url = data["url"]
            slug = slugify(url)

            contact = ContactManager.getContact(slug)

            if contact:
                contact.state = STATE_TRUSTED
                contact.key = data["key"]
                contact.name = data["name"]
                contact.save()

                #self.send_picture_to_contact(contact)
                self.return_success("Contact trusted.")

                for websocket_client in websocket_clients:
                    websocket_client.write_message(contact.toJson())

            else:
                self.return_failure("No contact for this slug.", 400)

        else:
            self.return_failure("Sent data are incorrects.", 400)

    def send_picture_to_contact(self, contact):
        user = UserManager.getUser()
        picture = user.fetch_attachment("small_picture.jpg")
        self.send_files_to_contact(
            contact,
            "contact/update-profile/picture/",
            fields={"key": user.key},
            files=[("smallpicture", "smallpicture.jpg", picture)]
        )


class ContactTagsHandler(NewebeAuthHandler):
    '''
    Tag operations: create, get, delete.
    '''

    def get(self):
        '''
        Returns the list of available tags.
        '''

        tags = ContactManager.getTags()
        tags.insert(0, ContactTag(name="all"))
        self.return_documents(tags)

    def post(self):
        '''
        Creates a new tag.
        '''

        data = self.get_body_as_dict(["name"])
        tag = ContactManager.getTagByName(data["name"])
        if tag is None:
            tag = ContactTag(name=data["name"])
            tag.save()
        self.return_one_document(tag, 201)

    def delete(self, id):
        '''
        Deletes given tag.
        '''

        tag = ContactManager.getTag(id)
        name = tag.name
        tag.delete()

        for contact in ContactManager.getTrustedContacts():
            if name in contact.tags:
                contact.tags.remove(name)
                contact.save()

        self.return_success("Tag successfully deleted.", 204)


class ContactTagHandler(NewebeAuthHandler):
    '''
    '''

    def put(self, slug):
        '''
        Grab tags sent inside request to set is on given contact.
        '''

        contact = ContactManager.getContact(slug)
        data = self.get_body_as_dict(["tags"])

        if contact:
            if data:
                contact.tags = data["tags"]
                contact.save()
            else:
                self.return_failure("No tags were sent")
        else:
            self.return_failure("Contact to modify does not exist.", 404)
