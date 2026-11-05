from retrieval import Retriever


def sample(text, brand='Bosch', manual='dishwasher'):
    return dict(id=manual+text, content=text, manual_id=manual, brand=brand, device_category='dishwasher')


def test_exact_error_aliases_and_unknown_manual():
    rows = [sample('E:24 waste water hose blocked'), sample('E240 unrelated fault'),
            sample('E24 drain', 'Other', 'other')]
    r = Retriever(rows)
    found = r.search('博世排水', brand='博世', error_code='E:24')
    assert len(found) == 1 and found[0]['content'].startswith('E:24')
    assert not r.search('E24', manual_id='unknown-model')
    assert not r.search('E999', error_code='E999')


def test_empty_and_unrelated_queries_abstain():
    assert Retriever([]).search('test') == []
    assert Retriever([sample('drain hose')]).search('zqxw') == []
    assert Retriever([sample('drain hose')]).search('drain', category='router') == []
