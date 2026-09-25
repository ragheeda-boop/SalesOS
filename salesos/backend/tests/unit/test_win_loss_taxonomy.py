from domains.commercial.opportunity.win_loss import normalize_loss_reason, summarize_win_loss


def test_loss_reason_taxonomy_is_stable_for_arabic_and_english_inputs():
    assert normalize_loss_reason("العميل اختار منافس") == "competitor"
    assert normalize_loss_reason("Budget frozen") == "price"
    assert normalize_loss_reason("") == "unclassified"


def test_win_loss_summary_preserves_unclassified_count():
    summary = summarize_win_loss(
        [
            {"status": "won"},
            {"status": "lost", "loss_reason": "competitor selected"},
            {"status": "closed_lost", "loss_reason": "Unknown"},
        ]
    )
    assert summary.won == 1
    assert summary.lost == 2
    assert summary.loss_reasons == {"competitor": 1, "unclassified": 1}
    assert summary.unclassified_losses == 1
