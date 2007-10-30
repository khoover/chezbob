from django.db import models

class Entity(models.Model):
    class Meta:
        db_table = 'cashout_entity'

    name = models.CharField(maxlength=256, blank=True)

    def __str__(self):
        return "%s" % self.name

    class Admin:
        ordering = ['name']


class CashOut(models.Model):
    class Meta:
        db_table = 'cashout_cashout'

    class Admin:
        pass

    datetime = models.DateTimeField('Collection Time')
    notes = models.TextField()

    def __str__(self):
        return "%s %s" % (self.datetime, self.notes)

    @classmethod
    def fetch_all(cls):
        from django.db import connection
        cursor = connection.cursor()

        entitys = {}
        for e in Entity.objects.all():
            entitys[e.id] = e

        result = []

        query = """SELECT cashout_cashout.id,
                          cashout_cashout.datetime,
                          cashout_cashout.notes,
                          cashout_cashcount.id,
                          cashout_cashcount.entity_id,
                          cashout_cashcount.total,
                          cashout_cashcount.memo
                   FROM cashout_cashout, cashout_cashcount, cashout_entity
                   WHERE cashout_cashcount.cashout_id = cashout_cashout.id
                         AND
                         cashout_cashcount.entity_id = cashout_entity.id
                   ORDER BY cashout_cashout.datetime,
                            cashout_entity.name"""
        cursor.execute(query)

        cashout = None
        for (id, datetime, notes, count_id, entity, total, memo) in cursor.fetchall():
            if cashout is None or cashout[0].id != id:
                if cashout is not None:
                    result.append(cashout)
                cashout = (CashOut(id=id, datetime=datetime, notes=notes), [])

            cashout[1].append(CashCount(id=count_id,
                                        cashout=cashout[0],
                                        entity=entitys[entity],
                                        total=total,
                                        memo=memo))

            # Mike's hack ommitted for now

        if cashout is not None:
            result.append(cashout)

        return result

    def delete(self):
        CashCount.objects.filter(cashout=self).delete()
        super(CashOut, self).delete() # Call the real save func


class CashCount(models.Model):
    class Meta:
        db_table = 'cashout_cashcount'

    class Admin:
        pass

    cashout = models.ForeignKey(CashOut)
    entity = models.ForeignKey(Entity)
    memo = models.CharField(maxlength=256, blank=True)

    bill100 = models.IntegerField('$100')
    bill50  = models.IntegerField('$50')
    bill20  = models.IntegerField('$20')
    bill10  = models.IntegerField('$10')
    bill5   = models.IntegerField('$5')
    bill1   = models.IntegerField('$1')
    coin100 = models.IntegerField('\xa2100') # \xa2 is cent symbol
    coin50  = models.IntegerField('\xa250')
    coin25  = models.IntegerField('\xa225')
    coin10  = models.IntegerField('\xa210')
    coin5   = models.IntegerField('\xa25')
    coin1   = models.IntegerField('\xa21')
    other   = models.FloatField(max_digits=12, decimal_places=2)
    total   = models.FloatField(max_digits=12, decimal_places=2, editable=False)

    def save(self):
        self.total = \
                self.bill100 * 100 +\
                self.bill50 * 50 +\
                self.bill20 * 20 +\
                self.bill10 * 10 +\
                self.bill5 * 5 +\
                self.bill1 * 1 +\
                self.coin100 +\
                self.coin50 * 0.50 +\
                self.coin25 * 0.25 +\
                self.coin10 * 0.10 +\
                self.coin5 * 0.05 +\
                self.coin1 * 0.01 +\
                self.other

        super(CashCount, self).save() # Call the real save func
