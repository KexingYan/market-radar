import SwiftUI

struct SettingsView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("数据状态") {
                    LabeledContent("Provider", value: "mock")
                    LabeledContent("真实行情", value: "未接入")
                    LabeledContent("交易功能", value: "未实现")
                    LabeledContent("推送通知", value: "未实现")
                }

                Section("安全边界") {
                    Text("手机客户端不保存券商密码，不直接连接券商桌面网关，不包含真实 API 密钥。")
                    Text("仅供信息展示，不构成投资建议。")
                }

                Section {
                    DisclaimerView()
                        .listRowInsets(EdgeInsets())
                        .listRowBackground(Color.clear)
                }
            }
            .navigationTitle("Settings")
        }
    }
}

#Preview {
    SettingsView()
}
