import {makeAutoObservable} from 'mobx';
import {handleApiFail} from 'js/utils';
import {ROOT_URL} from 'js/constants';
import {fetchGet} from 'jsapp/js/api';
import type {PaginatedResponse} from 'js/dataInterface';
import {BasePrice} from 'js/account/stripe.api';

const PRODUCTS_URL = '/api/v2/stripe/products/';
// For plan displaying purposes we only care about this part of the response
export interface BaseProduct {
  id: string;
  name: string;
  description: string;
  type: string;
  metadata: any;
}

export interface PlanInfo {
  product: BaseProduct;
  djstripe_created: string;
  djstripe_updated: string;
  id: string;
  livemode: boolean;
  created: string;
  metadata: {};
  description: string;
  active: boolean;
  aggregate_usage: string;
  amount: string;
  amount_decimal: string;
  billing_scheme: string;
  currency: string;
  interval: string;
  interval_count: 1;
  nickname: string;
  tiers: any;
  tiers_mode: string;
  transform_usage: any;
  trial_period_days: any;
  usage_type: string;
  djstripe_owner_account: string;
}

export interface SubscriptionInfo {
  plan: PlanInfo;
  djstripe_created: string;
  djstripe_updated: string;
  id: string;
  livemode: boolean;
  created: string;
  metadata: {};
  description: string;
  application_fee_percent: any;
  billing_cycle_anchor: string;
  billing_thresholds: any;
  cancel_at: any;
  cancel_at_period_end: boolean;
  canceled_at: any;
  collection_method: string;
  current_period_end: string;
  current_period_start: string;
  days_until_due: any;
  discount: any;
  ended_at: any;
  next_pending_invoice_item_invoice: any;
  pending_invoice_item_interval: any;
  pending_update: any;
  quantity: 1;
  start_date: string;
  status: string;
  trial_end: any;
  trial_start: any;
  djstripe_owner_account: string;
  customer: string;
  default_payment_method: string;
  default_source: any;
  latest_invoice: string;
  pending_setup_intent: any;
  schedule: any;
  default_tax_rates: [];
  items: {price: BasePrice}[];
}

// There is probably a better way to hand the nested types
export interface Product extends BaseProduct {
  prices: Array<PlanInfo>;
}

export async function fetchProducts() {
  return fetchGet<PaginatedResponse<Product>>(PRODUCTS_URL);
}

class SubscriptionStore {
  public planResponse: SubscriptionInfo[] = [];
  public addOnsResponse: SubscriptionInfo[] = [];
  public subscribedProduct: BaseProduct | null = null;
  public isPending = false;
  public isInitialised = false;

  constructor() {
    makeAutoObservable(this);
  }

  public fetchSubscriptionInfo() {
    if (this.isPending) {
      return;
    }
    this.isPending = true;
    $.ajax({
      dataType: 'json',
      method: 'GET',
      url: `${ROOT_URL}/api/v2/stripe/subscriptions/`,
    })
      .done(this.onFetchSubscriptionInfoDone.bind(this))
      .fail((response) => {
        this.isPending = false;
        handleApiFail(response);
      });
  }

  private onFetchSubscriptionInfoDone(
    response: PaginatedResponse<SubscriptionInfo>
  ) {
    // get any plan subscriptions for the user
    this.planResponse = response.results.filter(
      (sub) => sub.items[0]?.price.product.metadata?.product_type == 'plan'
    );
    // get any recurring add-on subscriptions for the user
    this.addOnsResponse = response.results.filter(
      (sub) => sub.items[0]?.price.product.metadata?.product_type == 'addon'
    );
    this.subscribedProduct =
      this.planResponse[0]?.items[0]?.price.product || null;
    this.isPending = false;
    this.isInitialised = true;
  }
}

export default new SubscriptionStore();
