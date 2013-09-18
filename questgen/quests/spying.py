# coding: utf-8

from questgen.quests.base_quest import BaseQuest
from questgen.facts import ( Start,
                             State,
                             Jump,
                             Finish,
                             Event,
                             Place,
                             Person,
                             LocatedIn,
                             LocatedNear,
                             Choice,
                             Option,
                             Message,
                             GivePower,
                             OptionsLink)


class Spying(BaseQuest):
    TYPE = 'spying'
    TAGS = ('normal', 'can_start', 'can_continue')

    # normal - normal quest
    # special - special quest
    # can_start - can be first quest in tree
    # can_continue - can be not first quest in tree

    @classmethod
    def construct_from_nothing(cls, knowledge_base, selector):
        return cls.construct_from_place(knowledge_base, selector, selector.new_place())

    @classmethod
    def construct_from_place(cls, knowledge_base, selector, start_place):
        return cls.construct_between_2(knowledge_base,
                                       selector,
                                       initiator=selector.person_from(places=(start_place, )),
                                       receiver=selector.new_person())

    @classmethod
    def construct_from_person(cls, knowledge_base, selector, initiator):
        return cls.construct_between_2(knowledge_base, selector, initiator, receiver=selector.new_person())

    @classmethod
    def construct_between_2(cls, knowledge_base, selector, initiator, receiver):
        return cls.construct( knowledge_base,
                              selector,
                              initiator=initiator,
                              initiator_position=selector.place_for(objects=(initiator,)),
                              receiver=receiver,
                              receiver_position=selector.place_for(objects=(receiver,)))

    @classmethod
    def construct(cls, knowledge_base, selector, initiator, initiator_position, receiver, receiver_position):

        hero_uid = selector.heroes()[0].uid

        ns = knowledge_base.get_next_ns()

        open_up_variants = Event(uid=ns+'open_up_variants', label=u'Варианты окончания раскрытия')

        start = Start(uid=ns+'start',
                      quest_type=cls.TYPE,
                      label=u'Начало',
                      description=u'Задание на шпионаж',
                      require=[LocatedIn(object=hero_uid, place=initiator_position),
                               LocatedIn(object=receiver, place=receiver_position)],
                      actions=[Message(id='intro')])

        start_spying = Choice(uid=ns+'start_spying',
                              label=u'Прибытие в город цели',
                              description=u'Герой прибывает к цели',
                              require=[LocatedIn(object=hero_uid, place=receiver_position)],
                              actions=[Message(id='arrived_to_target')])


        spying_middle = Choice(uid=ns+'spying_middle',
                               label=u'Шпионаж',
                               description=u'герой начинает шпионить',
                               actions=[Message(id='start_spying'),
                                        LocatedNear(object=hero_uid, place=receiver_position)])

        continue_spying = State(uid=ns+'continue_spying',
                                label=u'Продолжить шпионаж',
                                description=u'Герой шпионит за целью',
                                actions=[Message(id='continue_spying'),
                                         LocatedNear(object=hero_uid, place=receiver_position)])

        open_up = State(uid=ns+'open_up',
                        label=u'Раскрыться',
                        description=u'Сообщить цели о шпионаже',
                        require=[LocatedIn(object=hero_uid, place=receiver_position)],
                        actions=[Message(id='open_up')])


        report_data = Finish(uid=ns+'report_data',
                             label=u'Сообщить сообранную информацию',
                             description=u'Вернуться к нанивателю и сообщить собранную информацию',
                             require=[LocatedIn(object=hero_uid, place=initiator_position)],
                             actions=[Message(id='report_data'),
                                      GivePower(person=initiator, power=1),
                                      GivePower(person=receiver, power=-1)])

        open_up_finish = Finish(uid=ns+'open_up_finish',
                                label=u'Завершить задание',
                                description=u'Завершить задание и остатсья в городе цели',
                                tags=(open_up_variants.uid,),
                                require=[LocatedIn(object=hero_uid, place=receiver_position)],
                                actions=[Message(id='open_up_finish'),
                                      GivePower(person=initiator, power=-1),
                                      GivePower(person=receiver, power=1)])

        open_up_lying = Finish(uid=ns+'open_up_lying',
                               label=u'Обмануть заказчика',
                               description=u'Вернуться к заказчику и сообщить ложную информацию',
                               tags=(open_up_variants.uid,),
                               require=[LocatedIn(object=hero_uid, place=initiator_position)],
                               actions=[Message(id='open_up_lying'),
                                        GivePower(person=initiator, power=-1),
                                        GivePower(person=receiver, power=1)])

        start_spying__spying_middle = Option(state_from=start_spying.uid, state_to=spying_middle.uid)
        start_spying__open_up = Option(state_from=start_spying.uid, state_to=open_up.uid)

        spying_middle__continue_spying = Option(state_from=spying_middle.uid, state_to=continue_spying.uid)
        spying_middle__open_up = Option(state_from=spying_middle.uid, state_to=open_up.uid)


        facts = [ start,
                  start_spying,
                  spying_middle,
                  continue_spying,
                  open_up,
                  report_data,
                  open_up_finish,
                  open_up_lying,

                  Jump(state_from=start.uid, state_to=start_spying.uid),

                  start_spying__spying_middle,
                  start_spying__open_up,

                  spying_middle__continue_spying,
                  spying_middle__open_up,

                  Jump(state_from=continue_spying.uid, state_to=report_data.uid),

                  Jump(state_from=open_up.uid, state_to=open_up_finish.uid),
                  Jump(state_from=open_up.uid, state_to=open_up_lying.uid),

                  OptionsLink(options=(start_spying__open_up.uid, spying_middle__open_up.uid)),
                  OptionsLink(options=(start_spying__spying_middle.uid, spying_middle__continue_spying.uid)),

                  open_up_variants
                ]

        return facts
