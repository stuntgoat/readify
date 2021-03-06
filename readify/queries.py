#!/usr/bin/env python


import pymongo
import bson

from models import User, UserProfile


###
### Database config # put in settings abstraction eventually
###

DB_NAME = 'readify'


###
### Database Connection Handling
###

def init_db_conn(**kwargs):
    dbc = pymongo.Connection(**kwargs)
    db_conn = dbc[DB_NAME]
    return db_conn


def end_request(db_conn):
    """Here as a visual reminder that this funciton must be called at the end
    of a request to return the socket back to pymongo's built-in thread pooling.
    """
    return db_conn.end_request()


###
### Index Handling
###

def apply_all_indexes(db, indexes, collection):
    """Takes a list of indexes and applies them to a collection.

    Intended for use after functions that create/update/delete entire
    documents.
    """
    for index in indexes:
        db[collection].ensure_index(index)

    return True


###
### User Handling
###

USER_COLLECTION = 'users'
indexes_user = [
    [('username', pymongo.ASCENDING)],
]
    

def load_user(db, username=None, email=None):
    """Loads a user document from MongoDB.
    """
    query_dict = dict()
    if username:
        query_dict['username'] = '%s' % (username.lower())
    else:
        raise ValueError('Username field required')

    user_dict = db[USER_COLLECTION].find_one(query_dict)

    # In most cases, the python representation of the data is returned. User
    # documents are instantiated to provide access to commonly needed User
    # functions
    if user_dict is None:
        return None
    else:
        u = User(**user_dict)
        return u


def save_user(db, user):
    """Loads a user document from MongoDB.
    """
    user_doc = user.to_python()
    uid = db[USER_COLLECTION].insert(user_doc)
    user._id = uid

    apply_all_indexes(db, indexes_user, USER_COLLECTION)

    return uid


###
### UserProfile Handling
###

USERPROFILE_COLLECTION = 'userprofiles'
indexes_userprofile = [
    [('owner_id', pymongo.ASCENDING)],
    [('owner_username', pymongo.ASCENDING)],
]
    

def load_userprofile(db, owner_username=None, owner_id=None):
    """Loads a user document from MongoDB.
    """
    query_dict = dict()
    if owner_username:
        query_dict['owner_username'] = owner_username.lower()
    elif owner_id:
        query_dict['owner_id'] = owner_id
    else:
        raise ValueError('<owner_username> or <owner_id> field required')

    userprofile_dict = db[USERPROFILE_COLLECTION].find_one(query_dict)
    
    return userprofile_dict


def save_userprofile(db, userprofile):
    """Loads a user document from MongoDB.
    """
    userprofile_doc = userprofile.to_python()
    userprofile.id = db[USERPROFILE_COLLECTION].save(userprofile_doc)

    apply_all_indexes(db, indexes_userprofile, USERPROFILE_COLLECTION)

    return userprofile.id


###
### ListItem Handling
###

LISTITEM_COLLECTION = 'listitems'
indexes_listitem = [
    [('owner_id', pymongo.ASCENDING)],
    [('owner_username', pymongo.ASCENDING)],
]
    

def load_listitems(db, item_id=None, owner_id=None, owner_username=None,
                   archived=False, deleted=False, liked=None, tags=None,
                   updated_after=None):
    """Loads a user document from MongoDB.
    """
    query_dict = dict()
 
    ### One of these three fields is required for the primary index
    if owner_username:
        query_dict['owner_username'] = owner_username.lower()
    elif owner_id:
        query_dict['owner_id'] = owner_id
        # `item_id` isn't required. can be used with `owner` tho.
        if item_id:
            query_dict['_id'] = item_id
    else:
        raise ValueError('<owner_id> or <owner_username> field required')

    # These flags have defaults, but can be turned off with None
    if archived is not None:
        query_dict['archived'] = archived
    if deleted is not None:
        query_dict['deleted'] = deleted
    if liked is not None:
        query_dict['liked'] = liked
    if tags is not None and isinstance(tags, list):
        query_dict['tags'] = {'$all': tags}
    if updated_after is not None:
        query_dict['updated_at'] = {'$gte': updated_after}

    query_set = db[LISTITEM_COLLECTION].find(query_dict)
    return query_set

def save_listitem(db, item):
    """Loads a user document from MongoDB.
    """
    item_doc = item.to_python()
    item_id = db[LISTITEM_COLLECTION].save(item_doc)
    item._id = item_id

    apply_all_indexes(db, indexes_listitem, LISTITEM_COLLECTION)

    return item_id

def update_listitem(db, owner_id, item_id, archived=None, liked=None,
                    deleted=None):
    """`archive` should be boolean
    `like` should be boolean
    `delete` should be boolean
    """
    query_dict = {
        '_id': bson.objectid.ObjectId(unicode(item_id)), # string is given
        'owner_id': owner_id,
    }

    # One of these fields is required
    update_dict = dict()
    if archived is not None:
        update_dict['archived'] = archived
    elif liked is not None:
        update_dict['liked'] = liked
    elif deleted is not None:
        update_dict['deleted'] = deleted
    else:
        return None

    # TODO set updated_at
    db[LISTITEM_COLLECTION].update(query_dict, {'$set': update_dict})

    return True
