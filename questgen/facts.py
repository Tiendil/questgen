# coding: utf-8

import copy

from questgen import exceptions

######################
# Base class
######################

class Fact(object):
    _references = ()
    _attributes = {'uid': None,
                   'tags': (),
                   'label': None,
                   'description': None,
                   'exceptions': None,
                   'externals': None}
    _required = ()
    _serializable = ()

    def __init__(self, **kwargs):
        for name in self._required:
            if name not in kwargs:
                raise exceptions.RequiredAttributeError(fact=self.__class__,  attribute=name)
        for name, default in self._attributes.iteritems():
            setattr(self, name, kwargs.get(name, default))
        for name in kwargs.iterkeys():
            if name not in self._attributes:
                raise exceptions.WrongAttributeError(fact=self.__class__, attribute=name)
        self.update_uid()

    def serialize(self):
        data = {'class': self.__class__.__name__,
                'attributes': {attribute: getattr(self, attribute)
                               for attribute, default in self._attributes.iteritems()
                               if getattr(self, attribute) != default}}
        for attribute in self._serializable:
            if attribute not in data['attributes']:
                continue
            data['attributes'][attribute] = [fact.serialize() for fact in data['attributes'][attribute]]

        return data

    @classmethod
    def deserialize(cls, data, fact_classes):
        obj = cls(**data['attributes'])
        for attribute in cls._serializable:
            if attribute not in data['attributes']:
                continue
            setattr(obj,
                    attribute,
                    [fact_classes[fact_data['class']].deserialize(fact_data, fact_classes)
                     for fact_data in data['attributes'][attribute]])
        return obj

    def change(self, **kwargs):
        changed_fact = copy.deepcopy(self)
        for key, value in kwargs.items():
            if not hasattr(changed_fact, key):
                raise exceptions.WrongChangeAttributeError(fact=changed_fact, attribute=key)
            setattr(changed_fact, key, value)
        changed_fact.update_uid()
        return changed_fact

    def change_in_knowlege_base(self, knowledge_base, **kwargs):
        knowledge_base -= self
        knowledge_base += self.change(**kwargs)

    def check(self, knowledge_base):
        return self.uid in knowledge_base

    def update_uid(self):
        if self.uid is None:
            raise exceptions.UIDDidNotSetupped(fact=self)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and all(getattr(self, attribute) == getattr(other, attribute) for attribute in self._attributes.iterkeys())

    def __ne__(self, other):
        return not (self == other)

    @classmethod
    def type(cls): return cls.__name__

    def __repr__(self):
        return u'%s(%s)' % (self.type(),
                            u', '.join(u'%s=%r' % (attribute, getattr(self, attribute))
                                       for attribute, default in self._attributes.iteritems()
                                       if getattr(self, attribute) != default))

######################
# Base classes for different knowlege aspects
######################

class Action(Fact): pass

class Restriction(Fact): pass

class Actor(Fact): pass

class State(Fact):
    _attributes = dict(require=(), actions=(), **Fact._attributes)
    _serializable = ('require', 'actions')


class Jump(Fact):
    _references = ('state_from', 'state_to')
    _attributes = dict(state_from=None, state_to=None, **Fact._attributes)
    _required = tuple(['state_from', 'state_to'] + list(Fact._required))

    def update_uid(self):
        self.uid='#jump<%s, %s>' % (self.state_from, self.state_to)


class Condition(Fact): pass


class Pointer(Fact):
    UID = '#pointer'
    _references = ('state', 'jump')
    _attributes = dict(state=None, jump=None, **{attribute:(default if attribute != 'uid' else '#pointer')
                                                 for attribute, default in State._attributes.iteritems()})


class Event(Fact): pass

######################
# Concrete classes
######################


class Hero(Actor): pass

class Place(Actor):
    _attributes = dict(terrains=None, **Actor._attributes)

class Person(Actor):
    _attributes = dict(profession=None, **Actor._attributes)

class Mob(Actor):
    _attributes = dict(terrains=None, **Actor._attributes)

class Start(State):
    _attributes = dict(quest_type=None, **State._attributes)
    _required = tuple(['quest_type'] + list(State._required))

class Finish(State): pass

class Choice(State): pass

class Option(Jump):
    def update_uid(self):
        self.uid='#option<%s, %s>' % (self.state_from, self.state_to)

class OptionsLink(Fact):
    _attributes = dict(options=(), **Condition._attributes)
    _required = tuple(['options'] + list(Condition._required))

    def update_uid(self):
        self.uid='#options_link<%s>' % ','.join(self.options)


class ChoicePath(Fact):
    _references = ('choice', 'option')
    _attributes = dict(choice=None, option=None, default=None, **Condition._attributes)
    _required = tuple(['choice', 'option', 'default'] + list(Condition._required))

    def update_uid(self):
        self.uid = '#choice_path<%s, %s, %s>' % (self.choice, self.option, self.default)


class LocatedIn(Condition):
    _references = ('object', 'place')
    _attributes = dict(object=None, place=None, **Condition._attributes)
    _required = tuple(['object', 'place'] + list(Condition._required))

    @classmethod
    def relocate(cls, knowlege_base, object, new_place):
        location = filter(lambda fact: fact.object == object,
                          knowlege_base.filter(cls))[0]
        location.change_in_knowlege_base(knowlege_base, place=new_place)

    def update_uid(self):
        self.uid = '#located_in<%s, %s>' % (self.object, self.place)


class LocatedNear(Condition):
    _references = ('object', 'place')
    _attributes = dict(object=None, place=None, **Condition._attributes)
    _required = tuple(['object', 'place'] + list(Condition._required))

    def update_uid(self):
        self.uid = '#located_near<%s, %s>' % (self.object, self.place)


class Preference(Condition):
    _references = ('object',)

    def update_uid(self):
        self.uid = '#preference_%s<%s, %s>' % (self.preference, self.object, self.value)


class PreferenceMob(Preference):
    _references = ('object', 'mob')
    _attributes = dict(object=None, mob=None, **Preference._attributes)
    _required = tuple(['object', 'mob'] + list(Preference._required))

    def update_uid(self):
        self.uid = '#preference_mob<%s, %s>' % (self.object, self.mob)


class PreferenceHometown(Preference):
    _references = ('object', 'place')
    _attributes = dict(object=None, place=None, **Preference._attributes)
    _required = tuple(['object', 'place'] + list(Preference._required))

    def update_uid(self):
        self.uid = '#preference_place<%s, %s>' % (self.object, self.mob)



class PreferenceFriend(Preference):
    _references = ('object', 'person')
    _attributes = dict(object=None, person=None, **Preference._attributes)
    _required = tuple(['object', 'person'] + list(Preference._required))

    def update_uid(self):
        self.uid = '#preference_friend<%s, %s>' % (self.object, self.person)


class PreferenceEnemy(Preference):
    _references = ('object', 'person')
    _attributes = dict(object=None, person=None, **Preference._attributes)
    _required = tuple(['object', 'person'] + list(Preference._required))

    def update_uid(self):
        self.uid = '#preference_enemy<%s, %s>' % (self.object, self.person)



class PreferenceEquipmentSlot(Preference):
    _references = ('object',)
    _attributes = dict(object=None, equipment_slot=None, **Preference._attributes)
    _required = tuple(['object', 'equipment_slot'] + list(Preference._required))

    def update_uid(self):
        self.uid = '#preference_equipment_slot<%s, %s>' % (self.object, self.equipment_slot)


######################
# Actions classes
######################


class Message(Action):
    _attributes = dict(id=None, **Action._attributes)
    _required = tuple(['id'] + list(Action._required))

    def update_uid(self):
        self.uid = '#message<%s>' % self.id

class GivePower(Action):
    _references = ('person',)
    _attributes = dict(person=None, power=None, **Action._attributes)
    _required = tuple(['person', 'power'] + list(Action._required))

    def update_uid(self):
        self.uid = '#give_power<%s, %f>' % (self.person, self.power)


FACTS = {fact_class.type(): fact_class
         for fact_class in globals()
         if isinstance(fact_class, Fact) and issubclass(fact_class, Fact) and fact_class != Fact}


######################
# Restrictions classes
######################

class OnlyGoodBranches(Restriction):
    _references = ('person',)
    _attributes = dict(person=None, **Action._attributes)
    _required = tuple(['person'] + list(Action._required))

    def update_uid(self):
        self.uid = '#only_good_branches<%s>' % self.person

class OnlyBadBranches(Restriction):
    _references = ('person',)
    _attributes = dict(person=None, **Action._attributes)
    _required = tuple(['person'] + list(Action._required))

    def update_uid(self):
        self.uid = '#only_bad_branches<%s>' % self.person
